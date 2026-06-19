/**
 * 通知服务
 * 与后端 `app/api/v1/notifications.py` 对齐
 */

import { apiClient, type QueryParams } from './api'
import type { ListResponse } from '@/types'

/** 通知类型 */
export type NotificationType =
  | 'system'
  | 'trip_update'
  | 'comment'
  | 'like'
  | 'favorite'
  | 'job_complete'

/** 通知 */
export interface AppNotification {
  id: string
  user_id: string
  type: NotificationType
  title: string
  content: string | null
  is_read: boolean
  link_url: string | null
  created_at: string
  updated_at: string
}

export interface NotificationListQuery {
  user_id: string
  unread_only?: boolean
  page?: number
  page_size?: number
}

export function listNotifications(
  query: NotificationListQuery,
): Promise<ListResponse<AppNotification>> {
  const params: QueryParams = {
    user_id: query.user_id,
    unread_only: query.unread_only,
    page: query.page,
    page_size: query.page_size,
  }
  return apiClient.get<ListResponse<AppNotification>>('/notifications', params)
}

export function markAsRead(id: string, userId: string): Promise<AppNotification> {
  return apiClient.patch<AppNotification>(
    `/notifications/${id}/read`,
    undefined,
    { query: { user_id: userId } },
  )
}

export function markAllAsRead(userId: string): Promise<void> {
  return apiClient.post<void>('/notifications/read-all', undefined, {
    query: { user_id: userId },
  })
}

export function getUnreadCount(userId: string): Promise<{ unread_count: number }> {
  return apiClient.get<{ unread_count: number }>('/notifications/unread-count', {
    user_id: userId,
  })
}

export const notificationService = {
  listNotifications,
  markAsRead,
  markAllAsRead,
  getUnreadCount,
}

export default notificationService
