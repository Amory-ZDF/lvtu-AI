from dataclasses import dataclass
from typing import Protocol
from urllib.parse import quote_plus

from app.schemas.planning import (
    DestinationItem,
    DestinationRecommendationPayload,
    DestinationRecommendationRequest,
    ImageResource,
    MediaPlaceholderGroup,
    MediaPlaceholderPayload,
    MediaPlaceholderRequest,
    RouteDayPlan,
    RouteGenerationPayload,
    RouteGenerationRequest,
    RouteOption,
    RouteSpot,
)


@dataclass(slots=True)
class ProviderConfig:
    provider: str
    base_url: str | None
    api_key: str | None
    model_name: str | None = None


class RecommenderIntegration(Protocol):
    def recommend(
        self,
        request: DestinationRecommendationRequest,
    ) -> DestinationRecommendationPayload:
        ...


class RoutePlannerIntegration(Protocol):
    def generate_plan(
        self,
        request: RouteGenerationRequest,
    ) -> RouteGenerationPayload:
        ...


class MediaAssetIntegration(Protocol):
    def placeholders(
        self,
        request: MediaPlaceholderRequest,
    ) -> MediaPlaceholderPayload:
        ...


def _image_url(prompt: str, image_size: str = "landscape_16_9") -> str:
    encoded = quote_plus(prompt)
    return (
        "https://coresg-normal.trae.ai/api/ide/v1/text_to_image"
        f"?prompt={encoded}&image_size={image_size}"
    )


def _image_resource(category: str, subject: str, detail: str) -> ImageResource:
    prompt = (
        f"cinematic travel photography, {subject}, {detail}, natural light, "
        "editorial composition, realistic, high detail, premium travel website asset"
    )
    thumbnail_prompt = (
        f"travel photo thumbnail, {subject}, {detail}, realistic, clean composition"
    )
    return ImageResource(
        category=category,
        url=_image_url(prompt),
        thumbnail_url=_image_url(thumbnail_prompt, image_size="landscape_4_3"),
        alt=f"{subject} - {detail}",
        provider="mock-media",
        placeholder=True,
    )


class MockRecommendationIntegration:
    def recommend(
        self,
        request: DestinationRecommendationRequest,
    ) -> DestinationRecommendationPayload:
        season = request.season or "全年"
        styles = request.travel_style or ["慢游", "出片"]
        interests = request.interests or ["城市漫步", "咖啡", "摄影"]
        summary = (
            f"{request.duration_days} 天行程，季节偏好 {season}，"
            f"风格偏好 {'/'.join(styles)}，兴趣点 {'/'.join(interests[:3])}"
        )

        destinations = [
            DestinationItem(
                id="dest-kyoto",
                name="京都",
                country_or_region="日本",
                match_score=94,
                budget_range="4200-5800 RMB",
                best_season="11 月红叶 / 4 月樱花",
                vibe_tags=["寺院", "胶片感", "慢节奏"],
                reasons=["适合 3-5 天短途深度游", "拍照风格稳定", "步行和公共交通友好"],
                hero_image=_image_resource(
                    "destination",
                    "Kyoto temple street",
                    "autumn maple view",
                ),
                gallery=[
                    _image_resource(
                        "spot",
                        "Kyoto alley",
                        "traditional machiya and cafe",
                    ),
                    _image_resource("spot", "Kyoto shrine", "torii path in soft light"),
                ],
            ),
            DestinationItem(
                id="dest-chiangmai",
                name="清迈",
                country_or_region="泰国",
                match_score=89,
                budget_range="3200-4600 RMB",
                best_season="10 月到次年 2 月",
                vibe_tags=["手作", "夜市", "松弛感"],
                reasons=["预算更友好", "适合咖啡和市集路线", "适合朋友结伴"],
                hero_image=_image_resource(
                    "destination",
                    "Chiang Mai old town",
                    "lantern street at dusk",
                ),
                gallery=[
                    _image_resource(
                        "spot",
                        "Chiang Mai cafe",
                        "sunlit minimal cafe interior",
                    ),
                    _image_resource("spot", "Chiang Mai market", "night market candid scene"),
                ],
            ),
            DestinationItem(
                id="dest-yogyakarta",
                name="日惹",
                country_or_region="印度尼西亚",
                match_score=84,
                budget_range="3500-5200 RMB",
                best_season="5 月到 10 月",
                vibe_tags=["自然", "探险", "日出机位"],
                reasons=["适合火山和自然景观", "机位内容丰富", "路线辨识度高"],
                hero_image=_image_resource(
                    "destination",
                    "Yogyakarta volcano landscape",
                    "sunrise viewpoint",
                ),
                gallery=[
                    _image_resource(
                        "spot",
                        "Borobudur",
                        "misty sunrise with temple silhouette",
                    ),
                    _image_resource("spot", "Jeep trail", "adventure road in mountain light"),
                ],
            ),
        ]
        return DestinationRecommendationPayload(
            query_summary=summary,
            destinations=destinations,
        )


class MockRoutePlannerIntegration:
    def generate_plan(
        self,
        request: RouteGenerationRequest,
    ) -> RouteGenerationPayload:
        destination = request.destination_name
        duration = min(request.duration_days, 2)
        option_a = RouteOption(
            id="route-classic-first-timer",
            title=f"{destination} 经典初访覆盖线",
            pace=request.pace or "balanced",
            estimated_budget="5600 RMB",
            photo_score=8.6,
            summary="适合第一次来或旅行次数不多的人，优先覆盖经典地标和低决策成本动线。",
            days=[
                RouteDayPlan(
                    day=1,
                    theme="经典地标与核心街区",
                    commute_tip="将高热景点前置，避开中午人流高峰。",
                    spots=[
                        RouteSpot(
                            time_slot="上午",
                            name="经典地标",
                            description="第一次到访优先完成城市辨识度最高的地标。",
                            suggested_duration_hours=3.0,
                            images=[
                                _image_resource(
                                    "spot",
                                    f"{destination} landmark",
                                    "clean morning light",
                                )
                            ],
                        ),
                        RouteSpot(
                            time_slot="下午",
                            name="城市博物馆/展馆",
                            description="用室内展馆补足历史背景，也能平衡体力消耗。",
                            suggested_duration_hours=2.0,
                            images=[
                                _image_resource(
                                    "museum",
                                    f"{destination} museum",
                                    "quiet exhibition hall",
                                )
                            ],
                        ),
                    ],
                ),
                RouteDayPlan(
                    day=2,
                    theme="代表景区与轻松收尾",
                    commute_tip="把距离较远的代表景区放在同一天，减少跨城折返。",
                    spots=[
                        RouteSpot(
                            time_slot="上午",
                            name="代表景区",
                            description="覆盖最具代表性的自然或人文景区。",
                            suggested_duration_hours=3.0,
                            images=[
                                _image_resource(
                                    "spot",
                                    f"{destination} scenic area",
                                    "signature travel view",
                                )
                            ],
                        ),
                        RouteSpot(
                            time_slot="下午",
                            name="核心商圈/老街",
                            description="用餐饮和轻购物收尾，降低返程压力。",
                            suggested_duration_hours=2.0,
                            images=[
                                _image_resource(
                                    "citywalk",
                                    f"{destination} old street",
                                    "local street walk",
                                )
                            ],
                        ),
                    ],
                ),
            ][:duration],
        )
        option_b = RouteOption(
            id="route-repeat-visitor",
            title=f"{destination} 复访深度出片线",
            pace="relaxed",
            estimated_budget="4300 RMB",
            photo_score=9.2,
            summary="适合已经来过或旅行经验较多的人，减少经典重复，增加小众机位和慢体验。",
            days=[
                RouteDayPlan(
                    day=1,
                    theme="小众街区与日落机位",
                    commute_tip="围绕同一片区慢走，减少跨区移动。",
                    spots=[
                        RouteSpot(
                            time_slot="下午",
                            name="小众街区漫步",
                            description="避开常规打卡点，优先探索更在地的街巷和店铺。",
                            suggested_duration_hours=2.0,
                            images=[
                                _image_resource(
                                    "citywalk",
                                    f"{destination} hidden neighborhood",
                                    "quiet street walk",
                                )
                            ],
                        ),
                        RouteSpot(
                            time_slot="傍晚",
                            name="非热门日落机位",
                            description="利用日落前后 1 小时完成更有差异的照片。",
                            suggested_duration_hours=1.5,
                            images=[
                                _image_resource(
                                    "viewpoint",
                                    f"{destination} hidden sunset viewpoint",
                                    "golden hour city scene",
                                )
                            ],
                        ),
                    ],
                ),
                RouteDayPlan(
                    day=2,
                    theme="深度体验与松弛留白",
                    commute_tip="保留半天弹性时间，适合临时加点或二刷喜欢的区域。",
                    spots=[
                        RouteSpot(
                            time_slot="上午",
                            name="在地手作/市集",
                            description="用体验型内容替代纯景点打卡，增强复访新鲜感。",
                            suggested_duration_hours=2.0,
                            images=[
                                _image_resource(
                                    "spot",
                                    f"{destination} local market",
                                    "hands-on local experience",
                                )
                            ],
                        ),
                        RouteSpot(
                            time_slot="下午",
                            name="风格化咖啡/展览",
                            description="选择更适合慢坐和人像拍摄的室内空间。",
                            suggested_duration_hours=2.0,
                            images=[
                                _image_resource(
                                    "outfit",
                                    f"{destination} cafe portrait",
                                    "travel outfit styling",
                                )
                            ],
                        ),
                    ],
                ),
            ][:duration],
        )
        return RouteGenerationPayload(
            destination_name=destination,
            options=[option_a, option_b],
        )


class MockMediaAssetIntegration:
    def placeholders(
        self,
        request: MediaPlaceholderRequest,
    ) -> MediaPlaceholderPayload:
        categories = request.categories or ["destination", "viewpoint", "outfit"]
        destination = request.destination_name or "travel destination"
        assets = [
            MediaPlaceholderGroup(
                category=category,
                items=[
                    _image_resource(category, destination, f"{category} asset one"),
                    _image_resource(category, destination, f"{category} asset two"),
                ],
            )
            for category in categories
        ]
        return MediaPlaceholderPayload(
            destination_name=request.destination_name,
            assets=assets,
        )
