"""Production-oriented API for Nuclear Intelligence.

The service exposes liveness/readiness probes, research statistics, ledger
inspection and an on-demand cycle trigger. Existing endpoints are preserved;
security controls are opt-in through environment variables so local development
continues to work without credentials.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

from api.security import RateLimiter, configured_api_key, valid_bearer_token

logger = logging.getLogger("nuclear_intelligence.api")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

VERSION = "5.1.0"
START_TIME = time.time()
_core: Optional[Any] = None
_core_loading = False
_core_condition = threading.Condition()
_cycle_lock = threading.Lock()
_rate_limiter = RateLimiter(
    limit=int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60")),
    window_seconds=60,
)
_bearer = HTTPBearer(auto_error=False)


def _load_hf_core() -> Any:
    spec = importlib.util.spec_from_file_location(
        "hf_app", str(Path(__file__).parent.parent / "hf_deploy" / "app.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load HuggingFace deployment module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.core


def get_core() -> Optional[Any]:
    """Load the expensive core once, with a condition to avoid duplicate loads."""
    global _core, _core_loading
    with _core_condition:
        if _core is not None:
            return _core
        if _core_loading:
            _core_condition.wait(timeout=30)
            return _core
        _core_loading = True
    try:
        if os.getenv("SPACE_ID") or os.getenv("HF_SPACE"):
            loaded = _load_hf_core()
        else:
            from core.nuclear_intelligence import NuclearIntelligenceCore
            from blockchain.virtual_ledger import VirtualLedger
            loaded = {"core": NuclearIntelligenceCore(), "ledger": VirtualLedger()}
        with _core_condition:
            _core = loaded
        return loaded
    except Exception:
        logger.exception("Core initialization failed")
        return None
    finally:
        with _core_condition:
            _core_loading = False
            _core_condition.notify_all()


def _core_parts() -> tuple[Any, Any]:
    loaded = get_core()
    if loaded is None:
        raise HTTPException(status_code=503, detail="Core not initialized")
    if isinstance(loaded, dict):
        return loaded["core"], loaded["ledger"]
    return loaded, loaded.ledger


def _allowed_origins() -> List[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:7860,http://localhost:8000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title="Nuclear Intelligence API",
    description="Health, evidence-backed research, ledger statistics, and cycle triggers.",
    version=VERSION,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    client = request.client.host if request.client else "unknown"
    if os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true" and not _rate_limiter.allow(client):
        return Response(
            content='{"detail":"Rate limit exceeded"}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            media_type="application/json",
            headers={"Retry-After": "60", "X-Request-ID": request_id},
        )
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request error", extra={"request_id": request_id})
        raise
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-ms"] = f"{(time.perf_counter() - started) * 1000:.2f}"
    return response


async def require_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> None:
    expected = configured_api_key()
    if expected and not valid_bearer_token(
        f"{credentials.scheme} {credentials.credentials}" if credentials else None,
        expected,
    ):
        raise HTTPException(status_code=401, detail="Valid bearer API key required")


class CycleRequest(BaseModel):
    dev_mode: bool = True
    sync_to_hf: bool = True
    question: Optional[str] = Field(default=None, max_length=2_000)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = " ".join(value.split())
        return value or None


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: float
    version: str
    core_loaded: bool
    security: str


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "Nuclear Intelligence",
        "version": VERSION,
        "status": "operational",
        "endpoints": ["/health", "/ready", "/stats", "/chain", "/recent", "/search", "/metrics", "/governance", "/cycle"],
        "security": {"api_key_required": bool(configured_api_key()), "rate_limit_enabled": os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"},
        "github": "https://github.com/QalamHipHop/nuclear-intelligence",
        "huggingface": "https://huggingface.co/spaces/Qalam/Nuclear-Intelligence",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=round(time.time() - START_TIME, 3),
        version=VERSION,
        core_loaded=get_core() is not None,
        security="api-key" if configured_api_key() else "development-open",
    )


@app.get("/ready", dependencies=[Depends(require_api_key)])
def ready() -> Dict[str, Any]:
    core, _ = _core_parts()
    available = getattr(getattr(core, "llm", None), "_available", [])
    if not available or available == ["demo"]:
        raise HTTPException(status_code=503, detail="No LLM providers configured")
    return {"ready": True, "providers": available, "active_provider": getattr(core.llm, "_current", None)}


@app.get("/stats", dependencies=[Depends(require_api_key)])
def stats() -> Dict[str, Any]:
    core, _ = _core_parts()
    return core.get_stats()


@app.get("/chain", dependencies=[Depends(require_api_key)])
def chain() -> Dict[str, Any]:
    _, ledger = _core_parts()
    return ledger.get_stats()


@app.get("/recent", dependencies=[Depends(require_api_key)])
def recent(limit: int = Query(default=20, ge=1, le=200)) -> List[Dict[str, Any]]:
    core, _ = _core_parts()
    return core.history[-limit:][::-1]


@app.get("/search", dependencies=[Depends(require_api_key)])
def search(q: str = Query(min_length=2, max_length=300), limit: int = Query(default=10, ge=1, le=50)) -> List[Dict[str, Any]]:
    core, _ = _core_parts()
    return core.kg.search(" ".join(q.split()), limit)


@app.get("/metrics", dependencies=[Depends(require_api_key)])
def metrics() -> Dict[str, Any]:
    """Expose operational metrics without leaking provider credentials."""
    core, ledger = _core_parts()
    llm = getattr(core, "llm", None)
    llm_stats = getattr(llm, "stats", lambda: {})()
    chain_stats = ledger.get_stats()
    return {
        "version": VERSION,
        "uptime_seconds": round(time.time() - START_TIME, 3),
        "history_count": len(getattr(core, "history", [])),
        "llm": llm_stats,
        "ledger": {key: chain_stats.get(key) for key in ("nes_supply", "chain_length", "difficulty") if key in chain_stats},
    }


@app.get("/governance", dependencies=[Depends(require_api_key)])
def governance() -> Dict[str, Any]:
    """Return the persisted, non-secret research-controller summary."""
    reports_dir = Path(os.getenv("NI_REPORTS_DIR", Path(__file__).parent.parent / "reports"))
    summary_path = reports_dir / "governance_summary.json"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Governance summary not available yet")
    try:
        with summary_path.open("r", encoding="utf-8") as summary_file:
            return json.load(summary_file)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Governance summary unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Governance summary is temporarily unavailable") from exc


@app.post("/cycle", dependencies=[Depends(require_api_key)])
def trigger_cycle(req: CycleRequest) -> Dict[str, Any]:
    """Run one cycle; concurrent minting is rejected rather than interleaved."""
    core, _ = _core_parts()
    if not _cycle_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="A research cycle is already running")
    try:
        if req.question:
            return core.ask_question(req.question, dev_mode=req.dev_mode)
        result = core.run_cycle(dev_mode=req.dev_mode)
        if req.sync_to_hf and result.get("minted"):
            try:
                module = _load_hf_core()
                module.sync_to_hf_dataset(result)
            except Exception as exc:
                logger.warning("HF sync failed after successful cycle: %s", exc)
                result["hf_sync_error"] = str(exc)
        return result
    finally:
        _cycle_lock.release()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("API_HOST", "0.0.0.0"), port=int(os.getenv("API_PORT", "8000")))
