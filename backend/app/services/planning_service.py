from app.core.config import Settings
from app.integrations.factory import (
    get_media_asset_integration,
    get_recommender_integration,
    get_route_planner_integration,
)
from app.schemas.planning import (
    DestinationRecommendationPayload,
    DestinationRecommendationRequest,
    MediaPlaceholderPayload,
    MediaPlaceholderRequest,
    RouteGenerationPayload,
    RouteGenerationRequest,
)


def get_destination_recommendations(
    request: DestinationRecommendationRequest,
    settings: Settings,
) -> tuple[DestinationRecommendationPayload, str]:
    integration = get_recommender_integration(settings)
    return integration.recommend(request), settings.ai_provider


def get_route_generation(
    request: RouteGenerationRequest,
    settings: Settings,
) -> tuple[RouteGenerationPayload, str]:
    integration = get_route_planner_integration(settings)
    return integration.generate_plan(request), settings.agent_provider


def get_media_placeholders(
    request: MediaPlaceholderRequest,
    settings: Settings,
) -> tuple[MediaPlaceholderPayload, str]:
    integration = get_media_asset_integration(settings)
    return integration.placeholders(request), settings.media_provider
