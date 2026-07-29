from dataclasses import dataclass, field
from random import Random

from app.domain.models import CellState, Coordinate, GameStatus


@dataclass
class Board:
    width: int
    height: int
    mine_count: int
    mines: set[Coordinate]
    cells: dict[Coordinate, CellState] = field(default_factory=dict)
    status: GameStatus = GameStatus.IN_PROGRESS

    @classmethod
    def create(
        cls, width: int, height: int, mine_count: int, seed: int | None = None
    ) -> "Board":
        if width < 1 or height < 1:
            raise ValueError("board dimensions must be positive")
        if not 1 <= mine_count < width * height:
            raise ValueError("mine_count must leave at least one safe cell")

        coordinates = [
            Coordinate(row, column)
            for row in range(height)
            for column in range(width)
        ]
        mines = set(Random(seed).sample(coordinates, mine_count))
        return cls(
            width=width,
            height=height,
            mine_count=mine_count,
            mines=mines,
            cells={coordinate: CellState.HIDDEN for coordinate in coordinates},
        )

    @classmethod
    def from_mines(
        cls, width: int, height: int, mines: set[Coordinate]
    ) -> "Board":
        board = cls.create(width=width, height=height, mine_count=len(mines), seed=0)
        if any(not board.contains(coordinate) for coordinate in mines):
            raise ValueError("mine coordinate is outside the board")
        board.mines = mines
        return board

    def contains(self, cell: Coordinate) -> bool:
        return 0 <= cell.row < self.height and 0 <= cell.column < self.width

    def neighbors(self, cell: Coordinate) -> list[Coordinate]:
        self._require_inside(cell)
        return [
            Coordinate(row, column)
            for row in range(max(0, cell.row - 1), min(self.height, cell.row + 2))
            for column in range(max(0, cell.column - 1), min(self.width, cell.column + 2))
            if (row, column) != (cell.row, cell.column)
        ]

    def adjacent_mines(self, cell: Coordinate) -> int:
        return sum(neighbor in self.mines for neighbor in self.neighbors(cell))

    def _require_inside(self, cell: Coordinate) -> None:
        if not self.contains(cell):
            raise ValueError("cell is outside the board")
