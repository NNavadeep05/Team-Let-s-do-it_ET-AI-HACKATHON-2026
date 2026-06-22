from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router

def create_app() -> FastAPI:
    app = FastAPI(title="NEURON IQ API", version="1.0")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(auth_router, prefix="/api")
    app.include_router(documents_router, prefix="/api")
    
    @app.get("/api/health")
    async def health():
        return {"status": "ok", "env": settings.ENV}
        
    return app

