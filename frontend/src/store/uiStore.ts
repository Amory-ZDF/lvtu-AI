/**
 * UI 状态管理
 * - 侧边栏开合（移动端）
 * - 全局 loading
 * - toast 消息
 */

import { create } from 'zustand'

interface ToastMessage {
  id: number
  text: string
}

interface UIState {
  sidebarOpen: boolean
  globalLoading: boolean
  toasts: ToastMessage[]

  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void
  setGlobalLoading: (loading: boolean) => void
  showToast: (text: string, duration?: number) => void
  dismissToast: (id: number) => void
}

let toastId = 0

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  globalLoading: false,
  toasts: [],

  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setGlobalLoading: (globalLoading) => set({ globalLoading }),

  showToast: (text, duration = 2000) => {
    const id = ++toastId
    set((state) => ({ toasts: [...state.toasts, { id, text }] }))
    if (duration > 0) {
      setTimeout(() => {
        set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }))
      }, duration)
    }
  },

  dismissToast: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}))

export default useUIStore
