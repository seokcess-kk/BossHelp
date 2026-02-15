from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.v1 import router as v1_router
from app.api.admin import router as admin_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("BossHelp API starting...")
    yield
    # Shutdown
    print("BossHelp API shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="BossHelp API",
        description="AI-powered game guide Q&A API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    origins = settings.CORS_ORIGINS.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(v1_router)
    app.include_router(admin_router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "1.0.0"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
