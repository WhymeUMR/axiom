from pydantic import BaseModel, ConfigDict

from app.domain.models import CellState, GameStatus
from app.services.games import PublicCell, PublicGameState


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class CreateGameRequest(ApiModel):
    width: int
    height: int
    mine_count: int
    seed: int | None = None


class CellActionRequest(ApiModel):
    row: int
    column: int


class CellResponse(ApiModel):
    state: CellState
    adjacent_mines: int | None = None
    mine: bool | None = None

    @classmethod
    def from_domain(cls, cell: PublicCell) -> "CellResponse":
        return cls(
            state=cell.state,
            adjacent_mines=cell.adjacent_mines,
            mine=cell.mine,
        )


class GameStateResponse(ApiModel):
    id: str
    width: int
    height: int
    mine_count: int
    elapsed_seconds: int
    status: GameStatus
    grid: list[list[CellResponse]]

    @classmethod
    def from_domain(cls, state: PublicGameState) -> "GameStateResponse":
        return cls(
            id=state.id,
            width=state.width,
            height=state.height,
            mine_count=state.mine_count,
            elapsed_seconds=state.elapsed_seconds,
            status=state.status,
            grid=[[CellResponse.from_domain(cell) for cell in row] for row in state.grid],
        )
