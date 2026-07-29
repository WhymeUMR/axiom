import pytest

from app.domain.board import Board
from app.domain.models import CellState, Coordinate, GameFinishedError, GameStatus


def test_first_reveal_relocates_a_mine() -> None:
    board = Board.from_mines(width=2, height=2, mines={Coordinate(0, 0)})

    board.reveal(Coordinate(0, 0))

    assert board.status is GameStatus.IN_PROGRESS
    assert board.cells[Coordinate(0, 0)] is CellState.REVEALED
    assert Coordinate(0, 0) not in board.mines


def test_zero_reveal_floods_connected_safe_cells() -> None:
    board = Board.from_mines(width=4, height=4, mines={Coordinate(3, 3)})

    board.reveal(Coordinate(0, 0))

    assert board.cells[Coordinate(2, 2)] is CellState.REVEALED
    assert board.cells[Coordinate(3, 3)] is CellState.HIDDEN


def test_revealing_a_mine_loses_after_first_turn() -> None:
    board = Board.from_mines(width=3, height=3, mines={Coordinate(0, 0)})

    board.reveal(Coordinate(1, 1))
    board.reveal(Coordinate(0, 0))

    assert board.status is GameStatus.LOST
    assert board.cells[Coordinate(0, 0)] is CellState.REVEALED


def test_revealing_all_safe_cells_wins() -> None:
    board = Board.from_mines(width=2, height=2, mines={Coordinate(0, 0)})

    for cell in (Coordinate(0, 1), Coordinate(1, 0), Coordinate(1, 1)):
        board.reveal(cell)

    assert board.status is GameStatus.WON


def test_flag_toggles_without_revealing_cell() -> None:
    board = Board.from_mines(width=2, height=2, mines={Coordinate(0, 0)})

    board.toggle_flag(Coordinate(0, 0))

    assert board.cells[Coordinate(0, 0)] is CellState.FLAGGED


def test_finished_game_rejects_further_actions() -> None:
    board = Board.from_mines(width=2, height=2, mines={Coordinate(0, 0)})
    board.reveal(Coordinate(0, 1))
    board.reveal(Coordinate(1, 0))
    board.reveal(Coordinate(1, 1))

    with pytest.raises(GameFinishedError):
        board.toggle_flag(Coordinate(0, 0))
