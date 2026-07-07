export type OutfitGender = 'female' | 'male' | 'unisex'

function isGeneratedCard(url: string): boolean {
  return url.includes('/api/v1/media/place-card.svg')
}

function isStockOutfitImage(url: string): boolean {
  return url.includes('loremflickr.com')
}

export function inferOutfitGender(
  style: string,
  scene: string,
  items: Array<{ gender?: string; name?: string }> = [],
): OutfitGender {
  const explicitGenders = new Set(items.map((item) => item.gender?.toLowerCase()).filter(Boolean))
  if (explicitGenders.has('female') && !explicitGenders.has('male')) return 'female'
  if (explicitGenders.has('male') && !explicitGenders.has('female')) return 'male'

  const text = `${style} ${scene} ${items.map((item) => `${item.gender || ''} ${item.name || ''}`).join(' ')}`
  if (/女生|女士|女性|女装|womenswear|\bfemale\b/i.test(text)) return 'female'
  if (/男生|男士|男性|男装|menswear|\bmale\b/i.test(text)) return 'male'
  return 'unisex'
}

export function outfitGenderLabel(gender: OutfitGender): string {
  if (gender === 'male') return '男生推荐'
  if (gender === 'female') return '女生推荐'
  return '通用推荐'
}

export function resolveOutfitImage(
  images: string[],
): string {
  const existing = images.find((url) => url && !isGeneratedCard(url) && !isStockOutfitImage(url))
  return existing || ''
}

export function cssImageWithFallback(url: string, fallback: string): string {
  if (!url) return fallback
  return `url("${url}"), ${fallback}`
}
