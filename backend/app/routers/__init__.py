from backend.app.routers.vendors import router as vendors_router
from backend.app.routers.rfqs import router as rfqs_router
from backend.app.routers.quotations import router as quotations_router
from backend.app.routers.analysis import router as analysis_router
from backend.app.routers.purchase_orders import router as purchase_orders_router
from backend.app.routers.dashboard import router as dashboard_router

__all__ = [
    "vendors_router",
    "rfqs_router",
    "quotations_router",
    "analysis_router",
    "purchase_orders_router",
    "dashboard_router",
]
