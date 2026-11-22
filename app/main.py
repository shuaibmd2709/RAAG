import hmac
import json
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from app import embedder, store
from app.config import ADMIN_KEY, DAILY_ASK_CAP, DEFAULT_MENU, MAX_UPLOAD_MB, RATE_LIMIT_PER_MIN
from app.generate import answer
from app.loader import ScannedPdfError, extract_text
from app.parser import parse_menu
from app.ratelimit import RateLimiter
from app.schema import Menu

log = logging.getLogger("menu-bot")
limiter = RateLimiter(RATE_LIMIT_PER_MIN, DAILY_ASK_CAP)
_replace_lock = threading.Lock()


def ensure_index() -> None:
    try:
        store.vocab()
    except Exception:
        menu = Menu(**json.loads(Path(DEFAULT_MENU).read_text(encoding="utf-8")))
        store.replace_menu(menu)
        log.info("Indexed default menu (%s dishes)", len(menu.dishes))


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_index()
    embedder.embed(["warm-up"])          # load the model now, not on the first customer request
    yield


app = FastAPI(title="Restaurant Menu Assistant", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=300)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/menu")
def menu():
    return {"dishes": [d.model_dump() for d in store.all_dishes()]}


@app.post("/ask")
def ask(body: AskRequest, request: Request):
    question = body.question.strip()
    if not question:
        raise HTTPException(422, "Question is empty.")
    reason = limiter.check(request.client.host if request.client else "unknown")
    if reason:
        raise HTTPException(429, reason)
    try:
        return answer(question)
    except Exception:
        log.exception("ask failed")
        raise HTTPException(502, "The assistant is temporarily unavailable.")


@app.post("/upload")
def upload(file: UploadFile = File(...), x_admin_key: str | None = Header(default=None)):
    if not ADMIN_KEY or not x_admin_key or not hmac.compare_digest(x_admin_key, ADMIN_KEY):
        raise HTTPException(403, "Upload requires a valid admin key.")

    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(413, f"File larger than {MAX_UPLOAD_MB} MB.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(415, "Only PDF files are accepted.")

    try:
        text = extract_text(data)
    except ScannedPdfError as e:
        raise HTTPException(422, str(e))
    except Exception:
        raise HTTPException(422, "Could not read this PDF.")

    try:
        parsed, warnings = parse_menu(text)          # parse BEFORE touching the live index
    except Exception:
        log.exception("parse failed")
        raise HTTPException(502, "Menu parsing failed. The existing menu was not changed.")
    if not parsed.dishes:
        raise HTTPException(422, "No dishes found in this PDF. The existing menu was not changed.")

    with _replace_lock:
        count = store.replace_menu(parsed)
    return {"restaurant": parsed.restaurant, "dishes": count, "warnings": warnings}