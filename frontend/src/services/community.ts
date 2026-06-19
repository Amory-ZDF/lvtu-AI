/**
 * 社区服务
 * 与后端 `app/api/v1/core_business.py`（帖子）和 `interactions.py`（互动）对齐
 */

import { apiClient, type QueryParams } from './api'
import type {
  CommunityPost,
  CommunityPostCreate,
  CommunityPostUpdate,
  CommunityPostStatus,
  ListResponse,
} from '@/types'

/** 社区帖子列表查询参数 */
export interface CommunityPostListQuery {
  author_user_id?: string
  status?: CommunityPostStatus
  page?: number
  page_size?: number
}

/** 评论 */
export interface Comment {
  id: string
  post_id: string
  user_id: string
  content: string
  created_at: string
  updated_at: string
}

/** 评论创建请求 */
export interface CommentCreate {
  user_id: string
  content: string
}

// ── 帖子 CRUD ──

export function listPosts(
  query?: CommunityPostListQuery,
): Promise<ListResponse<CommunityPost>> {
  const params: QueryParams | undefined = query
    ? {
        author_user_id: query.author_user_id,
        status: query.status,
        page: query.page,
        page_size: query.page_size,
      }
    : undefined
  return apiClient.get<ListResponse<CommunityPost>>('/community-posts', params)
}

export function createPost(payload: CommunityPostCreate): Promise<CommunityPost> {
  return apiClient.post<CommunityPost>('/community-posts', payload)
}

export function getPost(postId: string): Promise<CommunityPost> {
  return apiClient.get<CommunityPost>(`/community-posts/${postId}`)
}

export function updatePost(
  postId: string,
  payload: CommunityPostUpdate,
): Promise<CommunityPost> {
  return apiClient.patch<CommunityPost>(`/community-posts/${postId}`, payload)
}

export function deletePost(postId: string): Promise<void> {
  return apiClient.delete<void>(`/community-posts/${postId}`)
}

// ── 点赞 ──

export function likePost(postId: string, userId: string): Promise<void> {
  return apiClient.post<void>(`/community-posts/${postId}/likes`, undefined, {
    query: { user_id: userId },
  })
}

export function unlikePost(postId: string, userId: string): Promise<void> {
  return apiClient.delete<void>(`/community-posts/${postId}/likes`, {
    query: { user_id: userId },
  })
}

// ── 评论 ──

export function listComments(
  postId: string,
  query?: { page?: number; page_size?: number },
): Promise<ListResponse<Comment>> {
  const params: QueryParams | undefined = query
    ? { page: query.page, page_size: query.page_size }
    : undefined
  return apiClient.get<ListResponse<Comment>>(`/community-posts/${postId}/comments`, params)
}

export function createComment(postId: string, payload: CommentCreate): Promise<Comment> {
  return apiClient.post<Comment>(`/community-posts/${postId}/comments`, payload)
}

export function deleteComment(commentId: string): Promise<void> {
  return apiClient.delete<void>(`/comments/${commentId}`)
}

// ── 收藏 ──

export function favoritePost(postId: string, userId: string): Promise<void> {
  return apiClient.post<void>(`/community-posts/${postId}/favorites`, undefined, {
    query: { user_id: userId },
  })
}

export function unfavoritePost(postId: string, userId: string): Promise<void> {
  return apiClient.delete<void>(`/community-posts/${postId}/favorites`, {
    query: { user_id: userId },
  })
}

export const communityService = {
  listPosts,
  createPost,
  getPost,
  updatePost,
  deletePost,
  likePost,
  unlikePost,
  listComments,
  createComment,
  deleteComment,
  favoritePost,
  unfavoritePost,
}

export default communityService
