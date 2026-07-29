from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from uuid import uuid4

from app.domain.board import Board
from app.domain.models import CellState, Coordinate, GameStatus


class GameNotFoundError(KeyError):
    """Raised when a game identifier is unknown."""


@dataclass(frozen=True)
class GameConfig:
    width: int
    height: int
    mine_count: int
    seed: int | None = None


@dataclass(frozen=True)
class PublicCell:
    state: CellState
    adjacent_mines: int | None
    mine: bool | None


@dataclass(frozen=True)
class PublicGameState:
    id: str
    width: int
    height: int
    mine_count: int
    elapsed_seconds: int
    status: GameStatus
    grid: tuple[tuple[PublicCell, ...], ...]


@dataclass
class GameRecord:
    id: str
    config: GameConfig
    board: Board
    started_at: float
    finished_at: float | None = None


class GameService:
    """Own active Minesweeper sessions and expose their public state."""

    def __init__(self, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._games: dict[str, GameRecord] = {}

    def create(self, config: GameConfig) -> PublicGameState:
        record = self._new_record(game_id=str(uuid4()), config=config)
        self._games[record.id] = record
        return self._snapshot(record)

    def get(self, game_id: str) -> PublicGameState:
        return self._snapshot(self._require_game(game_id))

    def reveal(self, game_id: str, cell: Coordinate) -> PublicGameState:
        record = self._require_game(game_id)
        record.board.reveal(cell)
        self._finish_if_needed(record)
        return self._snapshot(record)

    def toggle_flag(self, game_id: str, cell: Coordinate) -> PublicGameState:
        record = self._require_game(game_id)
        record.board.toggle_flag(cell)
        return self._snapshot(record)

    def restart(self, game_id: str) -> PublicGameState:
        record = self._require_game(game_id)
        replacement = self._new_record(game_id=record.id, config=record.config)
        self._games[game_id] = replacement
        return self._snapshot(replacement)

    def _new_record(self, game_id: str, config: GameConfig) -> GameRecord:
        return GameRecord(
            id=game_id,
            config=config,
            board=Board.create(
                width=config.width,
                height=config.height,
                mine_count=config.mine_count,
                seed=config.seed,
            ),
            started_at=self._clock(),
        )

    def _require_game(self, game_id: str) -> GameRecord:
        try:
            return self._games[game_id]
        except KeyError as error:
            raise GameNotFoundError(game_id) from error

    def _finish_if_needed(self, record: GameRecord) -> None:
        if record.board.status is not GameStatus.IN_PROGRESS and record.finished_at is None:
            record.finished_at = self._clock()

    def _snapshot(self, record: GameRecord) -> PublicGameState:
        now = record.finished_at if record.finished_at is not None else self._clock()
        reveal_mines = record.board.status is not GameStatus.IN_PROGRESS
        grid = tuple(
            tuple(
                self._public_cell(record.board, Coordinate(row, column), reveal_mines)
                for column in range(record.board.width)
            )
            for row in range(record.board.height)
        )
        return PublicGameState(
            id=record.id,
            width=record.board.width,
            height=record.board.height,
            mine_count=record.board.mine_count,
            elapsed_seconds=max(0, int(now - record.started_at)),
            status=record.board.status,
            grid=grid,
        )

    @staticmethod
    def _public_cell(board: Board, cell: Coordinate, reveal_mines: bool) -> PublicCell:
        state = board.cells[cell]
        adjacent_mines = board.adjacent_mines(cell) if state is CellState.REVEALED else None
        mine = cell in board.mines if reveal_mines else None
        return PublicCell(state=state, adjacent_mines=adjacent_mines, mine=mine)
