/**
 * i18n hook 封装
 * 在 useTranslation 基础上提供便捷的 t 与语言切换
 */

import { useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'

export interface UseI18nResult {
  t: TFunction
  i18n: ReturnType<typeof useTranslation>['i18n']
  /** 当前语言 */
  lng: string
  /** 切换语言 */
  changeLanguage: (lng: string) => Promise<unknown>
}

export function useI18n(): UseI18nResult {
  const { t, i18n } = useTranslation()
  const changeLanguage = useCallback(
    (next: string) => i18n.changeLanguage(next),
    [i18n],
  )
  return { t, i18n, lng: i18n.language, changeLanguage }
}

export default useI18n
