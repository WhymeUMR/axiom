from uuid import UUID

from app.services.games import GameConfig, GameService


def test_created_game_has_uuid_and_hidden_mines() -> None:
    service = GameService(clock=lambda: 100.0)

    game = service.create(GameConfig(width=9, height=9, mine_count=10, seed=3))

    assert UUID(game.id)
    assert all(cell.mine is None for row in game.grid for cell in row)
    assert game.elapsed_seconds == 0


def test_restart_keeps_the_same_settings_and_id() -> None:
    service = GameService(clock=lambda: 100.0)
    game = service.create(GameConfig(width=9, height=9, mine_count=10, seed=3))

    restarted = service.restart(game.id)

    assert restarted.id == game.id
    assert restarted.width == 9
    assert restarted.mine_count == 10
