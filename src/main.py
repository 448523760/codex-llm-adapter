from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from logging_config import configure_logging
from services.llm_proxy import proxy_response, proxy_response_stream
from utils.response_parser import parse_chat_completions_response


logger = logging.getLogger("codex_llm_adapter")


@asynccontextmanager
async def lifespan(_: FastAPI):
	configure_logging()
	logger.info("startup")
	yield
	logger.info("shutdown")


app = FastAPI(title="codex_llm_adapter", lifespan=lifespan)


@app.post("/response")
async def response_endpoint(payload: dict = Body(...)) -> object:
	try:
		stream = payload.get("stream", True)
		if isinstance(stream, bool) and stream:
			stream_iter = await proxy_response_stream(response_payload=payload)
			return StreamingResponse(stream_iter, media_type="text/event-stream")

		upstream = await proxy_response(response_payload=payload)
		return parse_chat_completions_response(upstream_payload=upstream)
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
