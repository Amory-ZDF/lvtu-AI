/**
 * 社区帖子类型定义
 * 与后端 `app/schemas/domain.py` 中的 CommunityPost 对齐
 */

/** 帖子状态 */
export type CommunityPostStatus = 'draft' | 'published' | 'archived'

/** 社区帖子 */
export interface CommunityPost {
  id: string
  author_user_id: string
  title: string
  content: string
  cover_image_url: string | null
  status: CommunityPostStatus
  like_count: number
  comment_count: number
  published_at: string | null
  created_at: string
  updated_at: string
}

/** 社区帖子创建请求 */
export interface CommunityPostCreate {
  author_user_id: string
  title: string
  content: string
  cover_image_url?: string | null
  status?: CommunityPostStatus
  published_at?: string | null
}

/** 社区帖子更新请求 */
export interface CommunityPostUpdate {
  author_user_id?: string
  title?: string
  content?: string
  cover_image_url?: string | null
  status?: CommunityPostStatus
  published_at?: string | null
  like_count?: number
  comment_count?: number
}

/** 社区帖子列表查询参数 */
export interface CommunityPostQuery {
  author_user_id?: string
  status?: CommunityPostStatus
  limit?: number
  offset?: number
}
