from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from logging_config import configure_logging


logger = logging.getLogger("codex_llm_adapter")


@asynccontextmanager
async def lifespan(_: FastAPI):
	configure_logging()
	logger.info("startup")
	yield
	logger.info("shutdown")


app = FastAPI(title="codex_llm_adapter", lifespan=lifespan)
