from .farmers import router as farmers_router
from .analysis import router as analysis_router
from .ml import router as ml_router

__all__ = ["farmers_router", "analysis_router", "ml_router"]
