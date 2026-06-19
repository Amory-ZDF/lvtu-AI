from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.responses import paginated_response, success_response
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.db.session import get_db_session
from app.middleware.auth import get_current_user_optional
from app.models.comment import Comment
from app.models.community_post import CommunityPost
from app.models.favorite import Favorite
from app.models.user import User
from app.models.user_behavior import UserBehavior
from app.schemas.common import ApiResponse
from app.schemas.interaction import (
    CommentCreate,
    CommentRead,
    FavoriteResponse,
    LikeResponse,
)

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]


def _get_post_or_404(db: Session, post_id: UUID) -> CommunityPost:
    post = db.get(CommunityPost, post_id)
    if post is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.COMMUNITY_POST_NOT_FOUND,
            message="社区帖子不存在",
        )
    return post


def _get_user_or_404(db: Session, user_id: UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.USER_NOT_FOUND,
            message="用户不存在",
        )
    return user


def _get_comment_or_404(db: Session, comment_id: UUID) -> Comment:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.NOT_FOUND,
            message="评论不存在",
        )
    return comment


def _record_behavior(
    db: Session,
    user_id: UUID,
    event_type: str,
    target_type: str,
    target_id: str,
    metadata: dict | None = None,
) -> None:
    behavior = UserBehavior(
        user_id=user_id,
        event_type=event_type,
        target_type=target_type,
        target_id=target_id,
        metadata_=metadata or {},
    )
    db.add(behavior)


def _has_liked(db: Session, user_id: UUID, post_id: UUID) -> bool:
    existing = db.scalar(
        select(UserBehavior).where(
            UserBehavior.user_id == user_id,
            UserBehavior.event_type == "like",
            UserBehavior.target_type == "community_post",
            UserBehavior.target_id == str(post_id),
        )
    )
    return existing is not None


@router.post(
    "/community-posts/{post_id}/likes",
    tags=["community-interactions"],
)
def like_post(
    post_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    user_id: UUID = Query(..., description="点赞用户 ID"),
) -> ApiResponse:
    post = _get_post_or_404(db, post_id)
    _get_user_or_404(db, user_id)

    already_liked = _has_liked(db, user_id, post_id)
    if not already_liked:
        post.like_count = (post.like_count or 0) + 1
        _record_behavior(
            db,
            user_id,
            event_type="like",
            target_type="community_post",
            target_id=str(post_id),
        )
        db.commit()
        db.refresh(post)

    return success_response(
        LikeResponse(
            post_id=post_id,
            user_id=user_id,
            like_count=post.like_count,
            liked=True,
        ).model_dump(mode="json"),
        request,
    )


@router.delete(
    "/community-posts/{post_id}/likes",
    tags=["community-interactions"],
)
def unlike_post(
    post_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    user_id: UUID = Query(..., description="取消点赞用户 ID"),
) -> ApiResponse:
    post = _get_post_or_404(db, post_id)
    _get_user_or_404(db, user_id)

    already_liked = _has_liked(db, user_id, post_id)
    if already_liked:
        post.like_count = max((post.like_count or 0) - 1, 0)
        _record_behavior(
            db,
            user_id,
            event_type="unlike",
            target_type="community_post",
            target_id=str(post_id),
        )
        db.commit()
        db.refresh(post)

    return success_response(
        LikeResponse(
            post_id=post_id,
            user_id=user_id,
            like_count=post.like_count,
            liked=False,
        ).model_dump(mode="json"),
        request,
    )


@router.get(
    "/community-posts/{post_id}/comments",
    tags=["community-interactions"],
)
def list_comments(
    post_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    _get_post_or_404(db, post_id)
    total = (
        db.scalar(
            select(func.count())
            .select_from(Comment)
            .where(Comment.post_id == post_id)
        )
        or 0
    )
    stmt = (
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.desc(), Comment.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    comments = list(db.scalars(stmt))
    items = [CommentRead.model_validate(c).model_dump(mode="json") for c in comments]
    return paginated_response(items, request, page=page, page_size=page_size, total=total)


@router.post(
    "/community-posts/{post_id}/comments",
    status_code=status.HTTP_201_CREATED,
    tags=["community-interactions"],
)
def create_comment(
    post_id: UUID,
    payload: CommentCreate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    post = _get_post_or_404(db, post_id)
    _get_user_or_404(db, payload.user_id)

    comment = Comment(
        post_id=post_id,
        user_id=payload.user_id,
        content=payload.content,
    )
    db.add(comment)
    post.comment_count = (post.comment_count or 0) + 1
    _record_behavior(
        db,
        payload.user_id,
        event_type="comment",
        target_type="community_post",
        target_id=str(post_id),
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.CONFLICT,
            message="评论创建失败",
        ) from exc
    db.refresh(comment)
    return success_response(
        CommentRead.model_validate(comment).model_dump(mode="json"),
        request,
    )


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["community-interactions"],
)
def delete_comment(
    comment_id: UUID,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> Response:
    comment = _get_comment_or_404(db, comment_id)
    post = db.get(CommunityPost, comment.post_id)
    db.delete(comment)
    if post is not None:
        post.comment_count = max((post.comment_count or 0) - 1, 0)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/community-posts/{post_id}/favorites",
    tags=["community-interactions"],
)
def favorite_post(
    post_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    user_id: UUID = Query(..., description="收藏用户 ID"),
) -> ApiResponse:
    _get_post_or_404(db, post_id)
    _get_user_or_404(db, user_id)

    existing = db.scalar(
        select(Favorite).where(
            Favorite.post_id == post_id,
            Favorite.user_id == user_id,
        )
    )
    if existing is None:
        favorite = Favorite(post_id=post_id, user_id=user_id)
        db.add(favorite)
        _record_behavior(
            db,
            user_id,
            event_type="favorite",
            target_type="community_post",
            target_id=str(post_id),
        )
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code=ErrorCode.CONFLICT,
                message="已收藏该帖子",
            ) from exc

    return success_response(
        FavoriteResponse(
            post_id=post_id,
            user_id=user_id,
            favorited=True,
        ).model_dump(mode="json"),
        request,
    )


@router.delete(
    "/community-posts/{post_id}/favorites",
    tags=["community-interactions"],
)
def unfavorite_post(
    post_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    user_id: UUID = Query(..., description="取消收藏用户 ID"),
) -> ApiResponse:
    _get_post_or_404(db, post_id)
    _get_user_or_404(db, user_id)

    existing = db.scalar(
        select(Favorite).where(
            Favorite.post_id == post_id,
            Favorite.user_id == user_id,
        )
    )
    if existing is not None:
        db.delete(existing)
        _record_behavior(
            db,
            user_id,
            event_type="unfavorite",
            target_type="community_post",
            target_id=str(post_id),
        )
        db.commit()

    return success_response(
        FavoriteResponse(
            post_id=post_id,
            user_id=user_id,
            favorited=False,
        ).model_dump(mode="json"),
        request,
    )
