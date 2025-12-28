def test_request_formatter_importable() -> None:
    from utils import request_formatter

    assert request_formatter is not None
