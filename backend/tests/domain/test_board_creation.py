from app.domain.board import Board
from app.domain.models import Coordinate


def test_seeded_board_has_requested_unique_mines() -> None:
    board = Board.create(width=9, height=9, mine_count=10, seed=7)

    assert len(board.mines) == 10
    assert len(set(board.mines)) == 10


def test_seeded_boards_are_reproducible() -> None:
    first = Board.create(width=9, height=9, mine_count=10, seed=7)
    second = Board.create(width=9, height=9, mine_count=10, seed=7)

    assert first.mines == second.mines


def test_adjacent_mine_count_is_correct() -> None:
    board = Board.from_mines(width=3, height=3, mines={Coordinate(0, 0), Coordinate(2, 2)})

    assert board.adjacent_mines(Coordinate(1, 1)) == 2
