def test_llm_proxy_importable() -> None:
    from services import llm_proxy

    assert llm_proxy is not None
