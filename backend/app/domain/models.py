from dataclasses import dataclass
from enum import StrEnum


class GameStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"


class CellState(StrEnum):
    HIDDEN = "hidden"
    REVEALED = "revealed"
    FLAGGED = "flagged"


class GameFinishedError(RuntimeError):
    """Raised when an action is attempted after a game has finished."""


@dataclass(frozen=True, order=True)
class Coordinate:
    row: int
    column: int
