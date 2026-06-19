from pydantic import BaseModel, Field


class ImageResource(BaseModel):
    category: str
    url: str
    thumbnail_url: str
    alt: str
    provider: str
    placeholder: bool = True


class DestinationRecommendationRequest(BaseModel):
    departure_city: str | None = None
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)
    duration_days: int = Field(default=4, ge=1, le=30)
    season: str | None = None
    travel_style: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)


class DestinationItem(BaseModel):
    id: str
    name: str
    country_or_region: str
    match_score: int
    budget_range: str
    best_season: str
    vibe_tags: list[str]
    reasons: list[str]
    hero_image: ImageResource
    gallery: list[ImageResource]


class DestinationRecommendationPayload(BaseModel):
    query_summary: str
    destinations: list[DestinationItem]


class RouteGenerationRequest(BaseModel):
    destination_id: str | None = None
    destination_name: str
    duration_days: int = Field(default=4, ge=1, le=30)
    pace: str = "balanced"
    travelers: int = Field(default=1, ge=1, le=20)
    interests: list[str] = Field(default_factory=list)


class RouteSpot(BaseModel):
    time_slot: str
    name: str
    description: str
    suggested_duration_hours: float
    images: list[ImageResource]


class RouteDayPlan(BaseModel):
    day: int
    theme: str
    commute_tip: str
    spots: list[RouteSpot]


class RouteOption(BaseModel):
    id: str
    title: str
    pace: str
    estimated_budget: str
    photo_score: float
    summary: str
    days: list[RouteDayPlan]


class RouteGenerationPayload(BaseModel):
    destination_name: str
    options: list[RouteOption]


class MediaPlaceholderRequest(BaseModel):
    categories: list[str] = Field(default_factory=list)
    destination_name: str | None = None
    keywords: list[str] = Field(default_factory=list)


class MediaPlaceholderGroup(BaseModel):
    category: str
    items: list[ImageResource]


class MediaPlaceholderPayload(BaseModel):
    destination_name: str | None = None
    assets: list[MediaPlaceholderGroup]
