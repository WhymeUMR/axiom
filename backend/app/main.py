from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import create_router
from app.services.games import GameService


def create_app() -> FastAPI:
    """Create the Minesweeper HTTP application."""
    app = FastAPI(title="Axiom Minesweeper API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(create_router(GameService()))
    return app


app = create_app()
