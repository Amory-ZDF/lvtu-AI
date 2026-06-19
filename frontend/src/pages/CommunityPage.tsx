/**
 * 社区页 (page-community)
 * 从后端拉取已发布的社区帖子，支持发帖（含封面图上传）
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorState } from '@/components/ErrorState'
import { EmptyState } from '@/components/EmptyState'
import { ImageUploader } from '@/components/ImageUploader'
import { LazyImage } from '@/components/LazyImage'
import { listPosts, createPost } from '@/services/community'
import { useAuthStore } from '@/store/authStore'
import { useUIStore } from '@/store/uiStore'
import type { CommunityPost } from '@/types'
import type { CommunityPostCard } from '@/data/mock'

/** 社区标签（前端过滤用） */
const COMMUNITY_TAGS = [
  '全部',
  '📸 拍照',
  '🍜 美食',
  '🏔️ 户外',
  '🏖️ 海边',
  '🏛️ 人文',
  '🧘 疗愈',
]

/** 渐变取色 */
const GRADIENTS = [
  'linear-gradient(135deg,oklch(0.65 0.12 22),oklch(0.57 0.15 45))',
  'linear-gradient(135deg,oklch(0.52 0.13 260),oklch(0.46 0.14 285))',
  'linear-gradient(135deg,oklch(0.58 0.15 170),oklch(0.50 0.13 198))',
  'linear-gradient(135deg,oklch(0.56 0.14 100),oklch(0.50 0.13 120))',
  'linear-gradient(135deg,oklch(0.60 0.15 340),oklch(0.52 0.16 5))',
  'linear-gradient(135deg,oklch(0.54 0.14 190),oklch(0.47 0.15 215))',
]

function pickGradient(id: string): string {
  let hash = 0
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) >>> 0
  return GRADIENTS[hash % GRADIENTS.length]
}

/** CommunityPost → CommunityPostCard */
function toCard(post: CommunityPost): CommunityPostCard {
  return {
    id: post.id,
    title: post.title,
    desc: post.content,
    author: post.author_user_id ? `用户 ${post.author_user_id.slice(-4)}` : '匿名用户',
    gradient: pickGradient(post.id),
    imageUrl: post.cover_image_url,
    clickable: true,
  }
}

export function CommunityPage() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const showToast = useUIStore((s) => s.showToast)

  const [activeTag, setActiveTag] = useState('全部')
  const [posts, setPosts] = useState<CommunityPost[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 发帖弹窗
  const [postModalOpen, setPostModalOpen] = useState(false)
  const [postTitle, setPostTitle] = useState('')
  const [postContent, setPostContent] = useState('')
  const [postCover, setPostCover] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const loadPosts = () => {
    setLoading(true)
    setError(null)
    listPosts({ status: 'published', page: 1, page_size: 20 })
      .then((res) => setPosts(res.items))
      .catch((err) => setError(err instanceof Error ? err.message : '获取帖子失败'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadPosts()
  }, [])

  const handlePostClick = (clickable?: boolean) => {
    if (clickable) {
      // 社区帖子暂无独立详情页，跳转首页
      navigate('/')
    }
  }

  /** 按标签前端过滤 */
  const filterByTag = (list: CommunityPostCard[], tag: string): CommunityPostCard[] => {
    if (tag === '全部') return list
    const keyword = tag.replace(/^[^\u4e00-\u9fa5a-zA-Z]+/, '')
    return list.filter(
      (p) => p.title.includes(keyword) || p.desc.includes(keyword),
    )
  }

  /** 模拟图片上传（后端暂无专用上传接口） */
  const handleUpload = (file: File): Promise<string> => {
    return new Promise((resolve) => {
      // 预留：后续接入真实上传接口时替换此处
      setTimeout(() => resolve(URL.createObjectURL(file)), 300)
    })
  }

  const openPostModal = () => {
    if (!isAuthenticated) {
      navigate('/login?redirect=/community')
      return
    }
    setPostTitle('')
    setPostContent('')
    setPostCover(null)
    setPostModalOpen(true)
  }

  const handleSubmitPost = async () => {
    if (!user) {
      showToast('请先登录')
      return
    }
    if (!postTitle.trim() || !postContent.trim()) {
      showToast('标题和内容不能为空')
      return
    }
    setSubmitting(true)
    try {
      await createPost({
        author_user_id: user.id,
        title: postTitle.trim(),
        content: postContent.trim(),
        cover_image_url: postCover,
        status: 'published',
        published_at: new Date().toISOString(),
      })
      showToast('发布成功')
      setPostModalOpen(false)
      loadPosts()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '发布失败')
    } finally {
      setSubmitting(false)
    }
  }

  const allCards = posts.map(toCard)
  const filteredCards = filterByTag(allCards, activeTag)

  return (
    <div className="page">
      <div className="community-header">
        <h2>💬 社区</h2>
        <p className="hint">看看大家都在去哪玩、怎么拍</p>
      </div>
      <div style={{ marginBottom: '16px' }}>
        <button className="btn btn-primary" onClick={openPostModal}>
          ✍️ 发帖
        </button>
      </div>
      <div className="community-tags">
        {COMMUNITY_TAGS.map((tag) => (
          <span
            key={tag}
            className={`chip${activeTag === tag ? ' selected' : ''}`}
            onClick={() => setActiveTag(tag)}
          >
            {tag}
          </span>
        ))}
      </div>
      {loading ? (
        <LoadingSpinner label="加载帖子中..." />
      ) : error ? (
        <ErrorState
          title="加载帖子失败"
          description={error}
          action={<button className="btn btn-primary" onClick={loadPosts}>重试</button>}
        />
      ) : filteredCards.length === 0 ? (
        <EmptyState
          icon="💬"
          title="暂无帖子"
          description={activeTag === '全部' ? '社区还没有内容，快来发第一篇帖子吧' : `没有「${activeTag}」相关的帖子`}
          action={
            activeTag !== '全部' ? (
              <button className="btn btn-primary" onClick={() => setActiveTag('全部')}>
                查看全部
              </button>
            ) : undefined
          }
        />
      ) : (
        <div className="community-grid">
          {filteredCards.map((post) => (
            <div
              key={post.id}
              className="post-card"
              onClick={() => handlePostClick(post.clickable)}
            >
              <div
                className="post-img"
                style={post.imageUrl ? undefined : { backgroundImage: post.gradient }}
              >
                {post.imageUrl && (
                  <LazyImage
                    src={post.imageUrl}
                    alt={post.title}
                    placeholder={post.gradient}
                    containerStyle={{ position: 'absolute', inset: 0 }}
                  />
                )}
              </div>
              <div className="post-body">
                <h4>{post.title}</h4>
                <p>{post.desc}</p>
              </div>
              <div className="post-author">
                <span className="pa"></span> {post.author}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 发帖弹窗 */}
      {postModalOpen && (
        <div
          className="detail-overlay show"
          onClick={(e) => e.target === e.currentTarget && setPostModalOpen(false)}
        >
          <div
            className="detail-panel"
            style={{ width: '480px', maxWidth: '94vw', maxHeight: '90vh', overflow: 'auto' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="dp-content" style={{ paddingTop: '24px' }}>
              <h2 style={{ fontSize: '1.15rem', marginBottom: '16px' }}>✍️ 发布帖子</h2>
              <div className="form-group" style={{ marginBottom: '12px' }}>
                <label>标题</label>
                <input
                  type="text"
                  placeholder="给你的帖子起个标题"
                  value={postTitle}
                  onChange={(e) => setPostTitle(e.target.value)}
                />
              </div>
              <div className="form-group" style={{ marginBottom: '12px' }}>
                <label>内容</label>
                <textarea
                  placeholder="分享你的旅行故事..."
                  value={postContent}
                  onChange={(e) => setPostContent(e.target.value)}
                  rows={4}
                  style={{ width: '100%', resize: 'vertical' }}
                />
              </div>
              <div style={{ marginBottom: '16px' }}>
                <ImageUploader
                  label="封面图"
                  onUpload={handleUpload}
                  value={postCover}
                  onChange={setPostCover}
                />
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  className="btn btn-secondary"
                  style={{ flex: 1, justifyContent: 'center' }}
                  onClick={() => setPostModalOpen(false)}
                >
                  取消
                </button>
                <button
                  className="btn btn-primary"
                  style={{ flex: 1, justifyContent: 'center' }}
                  disabled={submitting}
                  onClick={handleSubmitPost}
                >
                  {submitting ? '发布中...' : '发布'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CommunityPage
