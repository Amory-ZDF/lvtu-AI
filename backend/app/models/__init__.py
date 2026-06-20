from app.models.collaborator import Collaborator
from app.models.comment import Comment
from app.models.community_post import CommunityPost
from app.models.destination import Destination
from app.models.destination_candidate import DestinationCandidate
from app.models.favorite import Favorite
from app.models.generation_job import GenerationJob
from app.models.media_asset import MediaAsset
from app.models.notification import Notification
from app.models.outfit import Outfit
from app.models.outfit_recommendation import OutfitRecommendation
from app.models.packing_item import PackingItem
from app.models.photo_spot import PhotoSpot
from app.models.photo_spot_recommendation import PhotoSpotRecommendation
from app.models.plan_variant import PlanVariant
from app.models.trip import Trip
from app.models.trip_day import TripDay
from app.models.trip_point import TripPoint
from app.models.trip_version import TripVersion
from app.models.user import User
from app.models.user_behavior import UserBehavior
from app.models.user_preference import UserPreference

__all__ = [
    "Collaborator",
    "Comment",
    "CommunityPost",
    "Destination",
    "DestinationCandidate",
    "Favorite",
    "GenerationJob",
    "MediaAsset",
    "Notification",
    "Outfit",
    "OutfitRecommendation",
    "PackingItem",
    "PhotoSpot",
    "PhotoSpotRecommendation",
    "PlanVariant",
    "Trip",
    "TripDay",
    "TripPoint",
    "TripVersion",
    "User",
    "UserBehavior",
    "UserPreference",
]
