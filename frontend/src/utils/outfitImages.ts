const OUTFIT_BASE = 'https://loremflickr.com/960/540'

function stableHash(value: string): number {
  let hash = 0
  for (let i = 0; i < value.length; i++) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0
  }
  return hash
}

function outfitKeywords(scene: string, style: string): string {
  const text = `${scene} ${style}`.toLowerCase()
  if (/日落|观景|户外|自然|山|海|徒步|outdoor|hiking|sunset/.test(text)) {
    return 'outdoor,travel,outfit'
  }
  if (/城市|漫步|街|city|street/.test(text)) {
    return 'streetstyle,travel,outfit'
  }
  return 'travel,outfit,fashion'
}

function isGeneratedCard(url: string): boolean {
  return url.includes('/api/v1/media/place-card.svg')
}

export function outfitPhotoUrl(seed: string, scene: string, style: string): string {
  const lock = (stableHash(`${seed}-${scene}-${style}`) % 100000) + 1
  return `${OUTFIT_BASE}/${outfitKeywords(scene, style)}/all?lock=${lock}`
}

export function resolveOutfitImage(
  images: string[],
  seed: string,
  scene: string,
  style: string,
): string {
  const existing = images.find((url) => url && !isGeneratedCard(url))
  return existing || outfitPhotoUrl(seed, scene, style)
}

export function cssImageWithFallback(url: string, fallback: string): string {
  return `url("${url}"), ${fallback}`
}
