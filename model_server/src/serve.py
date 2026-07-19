"""Self-hosted text-generation server.

Wraps a local seq2seq model (default: google/flan-t5-small) behind a small
FastAPI service. The backend calls ``POST /infer`` with a fully-formed prompt.
Configuration is environment-driven so the same image works across
environments.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("model_server")

# Default to flan-t5-small: it is fast on CPU and, with the tuned decoding below,
# produces clean grounded answers. Set MODEL_NAME=google/flan-t5-base (or larger)
# on a GPU host for higher quality.
MODEL_NAME = os.getenv("MODEL_NAME", "google/flan-t5-small")
MAX_INPUT_TOKENS = int(os.getenv("MAX_INPUT_TOKENS", "1024"))
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "220"))
NUM_BEAMS = int(os.getenv("NUM_BEAMS", "1"))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))

_state: dict = {"model": None, "tokenizer": None}


class InferenceRequest(BaseModel):
    input_text: str = Field(..., min_length=1)
    max_new_tokens: int | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading model: %s", MODEL_NAME)
    _state["tokenizer"] = AutoTokenizer.from_pretrained(MODEL_NAME)
    _state["model"] = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    _state["model"].eval()
    logger.info("Model ready.")
    yield
    _state.clear()


app = FastAPI(title="Model Server", version="1.0.0", lifespan=lifespan)


@app.post("/infer")
async def infer(request: InferenceRequest):
    model, tokenizer = _state.get("model"), _state.get("tokenizer")
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model is not loaded yet.")

    try:
        inputs = tokenizer(
            request.input_text,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_INPUT_TOKENS,
        )
        with torch.no_grad():
            # Deterministic beam search keeps the (small) model faithful to the
            # retrieved context instead of sampling incoherent fragments.
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_new_tokens or MAX_NEW_TOKENS,
                min_new_tokens=24,
                num_beams=NUM_BEAMS,
                do_sample=False,
                early_stopping=True,
                # Keep a light repetition penalty only. Aggressive de-duplication
                # (no_repeat_ngram_size) corrupts legitimately repetitive content
                # such as price/airline lists ("... Visit Visa Starting from $...").
                repetition_penalty=1.1,
                length_penalty=1.0,
            )
        text = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        return JSONResponse(content={"response": text})
    except Exception as exc:  # noqa: BLE001
        logger.exception("Inference failed: %s", exc)
        raise HTTPException(status_code=500, detail="Inference failed.") from exc


@app.get("/health")
async def health():
    ready = _state.get("model") is not None
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "loading", "model": MODEL_NAME},
    )


@app.get("/")
async def root():
    return {"message": "Model server is running.", "model": MODEL_NAME}


if __name__ == "__main__":
    uvicorn.run("serve:app", host=HOST, port=PORT, reload=False)
