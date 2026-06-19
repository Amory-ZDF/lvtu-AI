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
        option_a = RouteOption(
            id="route-photo-relax",
            title=f"{destination} 高出片慢游线",
            pace="relaxed",
            estimated_budget="5600 RMB",
            photo_score=9.4,
            summary="围绕步行友好片区展开，兼顾经典打卡与停留时间。",
            days=[
                RouteDayPlan(
                    day=1,
                    theme="抵达适应与核心街区预热",
                    commute_tip="优先选择入住后步行覆盖的核心片区。",
                    spots=[
                        RouteSpot(
                            time_slot="下午",
                            name="入住周边漫步",
                            description="先熟悉街区节奏，安排轻量打卡和咖啡店。",
                            suggested_duration_hours=2.0,
                            images=[
                                _image_resource(
                                    "spot",
                                    f"{destination} neighborhood",
                                    "quiet street walk",
                                )
                            ],
                        ),
                        RouteSpot(
                            time_slot="傍晚",
                            name="黄金时段拍摄点",
                            description="利用日落前后 1 小时完成首轮出片。",
                            suggested_duration_hours=1.5,
                            images=[
                                _image_resource(
                                    "viewpoint",
                                    f"{destination} sunset viewpoint",
                                    "golden hour city scene",
                                )
                            ],
                        ),
                    ],
                ),
                RouteDayPlan(
                    day=2,
                    theme="经典景点与深度体验",
                    commute_tip="将高热景点前置，避开中午人流高峰。",
                    spots=[
                        RouteSpot(
                            time_slot="上午",
                            name="经典地标",
                            description="早到减少排队时间，并保留宽松拍照节奏。",
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
                            name="风格化咖啡/展览",
                            description="补充室内体验，平衡体力消耗。",
                            suggested_duration_hours=2.5,
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
            ],
        )
        option_b = RouteOption(
            id="route-efficient",
            title=f"{destination} 效率打卡线",
            pace="compact",
            estimated_budget="4300 RMB",
            photo_score=8.6,
            summary="优先覆盖核心地标，适合天数更少或首次到访。",
            days=option_a.days[: min(len(option_a.days), request.duration_days)],
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
