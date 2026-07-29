from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create the Minesweeper HTTP application."""
    return FastAPI(title="Axiom Minesweeper API")


app = create_app()
