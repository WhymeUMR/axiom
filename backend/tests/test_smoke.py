def test_backend_package_is_importable() -> None:
    from app.main import create_app

    assert callable(create_app)
