const OUTFIT_BASE = 'https://loremflickr.com/960/540'

export type OutfitGender = 'female' | 'male' | 'unisex'

function stableHash(value: string): number {
  let hash = 0
  for (let i = 0; i < value.length; i++) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0
  }
  return hash
}

function outfitKeywords(scene: string, style: string, gender: OutfitGender): string {
  const text = `${scene} ${style}`.toLowerCase()
  const genderKeyword = gender === 'male' ? 'menswear' : gender === 'female' ? 'womenswear' : 'outfit'
  if (/日落|观景|户外|自然|山|海|徒步|outdoor|hiking|sunset/.test(text)) {
    return `outdoor,travel,${genderKeyword}`
  }
  if (/城市|漫步|街|city|street/.test(text)) {
    return `streetstyle,travel,${genderKeyword}`
  }
  return `travel,${genderKeyword},fashion`
}

function isGeneratedCard(url: string): boolean {
  return url.includes('/api/v1/media/place-card.svg')
}

export function inferOutfitGender(
  style: string,
  scene: string,
  items: Array<{ gender?: string; name?: string }> = [],
): OutfitGender {
  const text = `${style} ${scene} ${items.map((item) => `${item.gender || ''} ${item.name || ''}`).join(' ')}`
  if (/男生|男士|男性|menswear|male/i.test(text)) return 'male'
  if (/女生|女士|女性|womenswear|female/i.test(text)) return 'female'
  return 'unisex'
}

export function outfitGenderLabel(gender: OutfitGender): string {
  if (gender === 'male') return '男生推荐'
  if (gender === 'female') return '女生推荐'
  return '通用推荐'
}

export function outfitPhotoUrl(
  seed: string,
  scene: string,
  style: string,
  gender: OutfitGender = 'unisex',
): string {
  const lock = (stableHash(`${seed}-${scene}-${style}-${gender}`) % 100000) + 1
  return `${OUTFIT_BASE}/${outfitKeywords(scene, style, gender)}/all?lock=${lock}`
}

export function resolveOutfitImage(
  images: string[],
  seed: string,
  scene: string,
  style: string,
  gender: OutfitGender = 'unisex',
): string {
  const existing = images.find((url) => url && !isGeneratedCard(url))
  return existing || outfitPhotoUrl(seed, scene, style, gender)
}

export function cssImageWithFallback(url: string, fallback: string): string {
  return `url("${url}"), ${fallback}`
}

export function buildOutfitImagePrompt(params: {
  destinationName?: string
  gender: OutfitGender
  scene: string
  season: string
  style: string
  items: string[]
}): string {
  const subject =
    params.gender === 'male'
      ? 'an adult male traveler'
      : params.gender === 'female'
        ? 'an adult female traveler'
        : 'an adult traveler'
  const destination = params.destinationName || 'the travel destination'
  const items = params.items.join(', ')
  return [
    `Create a photorealistic full-body travel outfit preview of ${subject}.`,
    `Scene: ${params.scene} in ${destination}. Season/weather context: ${params.season}.`,
    `Outfit style: ${params.style}. Key clothing items: ${items}.`,
    'Natural standing pose, realistic body proportions, comfortable travel look, practical shoes, layered styling.',
    'Use a real travel background that matches the scene, soft natural light, editorial lookbook composition.',
    'Do not include text, logos, brand marks, watermarks, distorted hands, duplicated limbs, or exaggerated fashion runway styling.',
    'Image ratio 3:4 vertical, medium-wide shot, clear view of the outfit.',
  ].join(' ')
}
