def test_app_importable() -> None:
    from main import app

    assert app is not None
