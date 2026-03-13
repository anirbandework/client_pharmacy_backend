"""Admin routes, analytics, and AI services for invoice analyzer"""

from .admin_routes import router
from .admin_dependencies import get_admin_with_org
from .admin_ai_analytics_service import InvoiceAIAnalytics
from .dashboard_analytics import DashboardAnalytics

__all__ = [
    "router",
    "get_admin_with_org",
    "InvoiceAIAnalytics",
    "DashboardAnalytics",
]
