from fastapi import APIRouter
from src.api.v1 import auth, dataset, user, query, insight

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(dataset.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(query.router, prefix="/queries", tags=["queries"])
api_router.include_router(insight.router, prefix="/insights", tags=["insights"])
