from fastapi.testclient import TestClient

from app import main
from app.ratelimit import RateLimiter

client = TestClient(main.app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_validation():
    assert client.post("/ask", json={"question": ""}).status_code == 422
    assert client.post("/ask", json={"question": "x" * 301}).status_code == 422


def test_ask_rate_limited(monkeypatch):
    monkeypatch.setattr(main, "limiter", RateLimiter(1, 100))
    monkeypatch.setattr(main, "answer", lambda q: {"answer": "ok", "plan": {}, "sources": []})
    assert client.post("/ask", json={"question": "hi"}).status_code == 200
    assert client.post("/ask", json={"question": "hi"}).status_code == 429


def test_upload_disabled_without_admin_key(monkeypatch):
    monkeypatch.setattr(main, "ADMIN_KEY", None)
    r = client.post("/upload", files={"file": ("m.pdf", b"%PDF-1.4")}, headers={"X-Admin-Key": "x"})
    assert r.status_code == 403


def test_upload_requires_correct_key(monkeypatch):
    monkeypatch.setattr(main, "ADMIN_KEY", "secret")
    r = client.post("/upload", files={"file": ("m.pdf", b"%PDF-1.4")}, headers={"X-Admin-Key": "wrong"})
    assert r.status_code == 403


def test_upload_rejects_non_pdf(monkeypatch):
    monkeypatch.setattr(main, "ADMIN_KEY", "secret")
    r = client.post("/upload", files={"file": ("m.pdf", b"hello")}, headers={"X-Admin-Key": "secret"})
    assert r.status_code == 415

def test_index_page_served():
    r = client.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]