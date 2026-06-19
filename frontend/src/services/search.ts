/**
 * 搜索服务
 * 与后端 `app/api/v1/search.py` 对齐
 */

import { apiClient, type QueryParams } from './api'
import type { ListResponse } from '@/types'

/** 搜索类型 */
export type SearchType = 'destination' | 'post' | 'spot' | 'all'

/** 搜索结果项（通用结构） */
export interface SearchResultItem {
  id: string
  type: SearchType
  title: string
  snippet?: string | null
  image_url?: string | null
  [key: string]: unknown
}

export interface SearchQuery {
  keyword: string
  type?: SearchType
  page?: number
  page_size?: number
}

export function search(query: SearchQuery): Promise<ListResponse<SearchResultItem>> {
  const params: QueryParams = {
    keyword: query.keyword,
    type: query.type,
    page: query.page,
    page_size: query.page_size,
  }
  return apiClient.get<ListResponse<SearchResultItem>>('/search', params)
}

export const searchService = {
  search,
}

export default searchService
