"""Staff routes and dependencies for invoice analyzer"""

from .staff_routes import router
from .staff_dependencies import get_current_user_with_geofence

__all__ = ["router", "get_current_user_with_geofence"]
