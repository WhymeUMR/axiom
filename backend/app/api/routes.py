from collections.abc import Callable

from fastapi import APIRouter, HTTPException, status

from app.api.schemas import CellActionRequest, CreateGameRequest, GameStateResponse
from app.domain.models import Coordinate, GameFinishedError
from app.services.games import (
    GameConfig,
    GameNotFoundError,
    GameService,
    PublicGameState,
)


def create_router(service: GameService) -> APIRouter:
    router = APIRouter(prefix="/api/games", tags=["games"])

    @router.post(
        "",
        response_model=GameStateResponse,
        response_model_exclude_none=True,
        status_code=status.HTTP_201_CREATED,
    )
    def create_game(request: CreateGameRequest) -> GameStateResponse:
        try:
            game = service.create(
                GameConfig(
                    width=request.width,
                    height=request.height,
                    mine_count=request.mine_count,
                    seed=request.seed,
                )
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
        return GameStateResponse.from_domain(game)

    @router.get(
        "/{game_id}", response_model=GameStateResponse, response_model_exclude_none=True
    )
    def get_game(game_id: str) -> GameStateResponse:
        return _state_or_error(lambda: service.get(game_id))

    @router.post(
        "/{game_id}/reveal", response_model=GameStateResponse, response_model_exclude_none=True
    )
    def reveal(game_id: str, request: CellActionRequest) -> GameStateResponse:
        return _state_or_error(
            lambda: service.reveal(game_id, Coordinate(row=request.row, column=request.column))
        )

    @router.post(
        "/{game_id}/flag", response_model=GameStateResponse, response_model_exclude_none=True
    )
    def toggle_flag(game_id: str, request: CellActionRequest) -> GameStateResponse:
        return _state_or_error(
            lambda: service.toggle_flag(game_id, Coordinate(row=request.row, column=request.column))
        )

    @router.post(
        "/{game_id}/restart", response_model=GameStateResponse, response_model_exclude_none=True
    )
    def restart(game_id: str) -> GameStateResponse:
        return _state_or_error(lambda: service.restart(game_id))

    return router


def _state_or_error(action: Callable[[], PublicGameState]) -> GameStateResponse:
    try:
        state = action()
    except GameNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="game not found") from error
    except GameFinishedError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="game has finished") from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    return GameStateResponse.from_domain(state)
