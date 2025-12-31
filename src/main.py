from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from logging_config import configure_logging
from services.llm_proxy import proxy_response_stream


logger = logging.getLogger("codex_llm_adapter")


@asynccontextmanager
async def lifespan(_: FastAPI):
	configure_logging()
	logger.info("startup")
	yield
	logger.info("shutdown")


app = FastAPI(title="codex_llm_adapter", lifespan=lifespan)


@app.post("/response")
async def response_endpoint(payload: dict = Body(...)) -> StreamingResponse:
	try:
		stream = payload.get("stream")
		if stream is not True:
			raise HTTPException(
				status_code=400, detail="The stream parameter must be true; non-streaming is unsupported."
			)

		stream_iter = await proxy_response_stream(response_payload=payload)
		return StreamingResponse(stream_iter, media_type="text/event-stream")
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
