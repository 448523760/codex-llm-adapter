def test_response_parser_importable() -> None:
    from utils import response_parser

    assert response_parser is not None
