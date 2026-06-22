"""
Nuclear Intelligence v5.0 - Health Check API
═══════════════════════════════════════════════════════════════════
FastAPI service exposing system health, statistics, and a manual
cycle trigger endpoint. Use for monitoring + on-demand research.

Endpoints:
- GET  /                → service info
- GET  /health          → liveness probe (returns 200 if alive)
- GET  /ready           → readiness probe (returns 200 if LLM is configured)
- GET  /stats           → full system statistics
- GET  /chain           → blockchain stats
- GET  /recent          → recent cycle history
- GET  /search?q=...    → search knowledge graph
- POST /cycle           → trigger a research cycle
═══════════════════════════════════════════════════════════════════
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Try to import the core; fall back to lazy import
_core: Optional[Any] = None
_core_lock = False


def get_core():
    """Lazy load the core (HF or full) so the API can start quickly."""
    global _core, _core_lock
    if _core is not None:
        return _core
    if _core_lock:
        return None
    _core_lock = True
    try:
        if os.getenv("SPACE_ID") or os.getenv("HF_SPACE"):
            # Use HF self-contained core
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "hf_app",
                str(Path(__file__).parent.parent / "hf_deploy" / "app.py"),
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _core = mod.core
        else:
            from core.nuclear_intelligence import NuclearIntelligenceCore
            from blockchain.virtual_ledger import VirtualLedger
            _core = {
                "core": NuclearIntelligenceCore(),
                "ledger": VirtualLedger(),
            }
    except Exception as e:
        print(f"Core init failed: {e}")
        _core = None
    finally:
        _core_lock = False
    return _core


app = FastAPI(
    title="Nuclear Intelligence API",
    description="Health, statistics, and cycle triggers for the Nuclear Intelligence pipeline.",
    version="5.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Models ──────────────────────────────────────────────────────

class CycleRequest(BaseModel):
    dev_mode: bool = True
    sync_to_hf: bool = True
    question: Optional[str] = None  # if set, ask directly instead of full cycle


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: float
    version: str
    core_loaded: bool


START_TIME = time.time()
VERSION = "5.0.0"


# ─── Routes ──────────────────────────────────────────────────────

@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "Nuclear Intelligence",
        "version": VERSION,
        "endpoints": ["/health", "/ready", "/stats", "/chain", "/recent", "/search", "/cycle"],
        "github": "https://github.com/QalamHipHop/nuclear-intelligence",
        "huggingface": "https://huggingface.co/spaces/Qalam/Nuclear-Intelligence",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat(),
        uptime_seconds=time.time() - START_TIME,
        version=VERSION,
        core_loaded=get_core() is not None,
    )


@app.get("/ready")
def ready() -> Dict[str, Any]:
    """Readiness probe: returns 200 only if the core is fully initialized with at least one LLM provider."""
    core = get_core()
    if core is None:
        raise HTTPException(status_code=503, detail="Core not initialized")
    # Check that at least one non-demo LLM provider is available
    if isinstance(core, dict):
        llm = core["core"].llm
    else:
        llm = core.llm
    available = llm._available
    if not available or available == ["demo"]:
        raise HTTPException(status_code=503, detail="No LLM providers configured")
    return {
        "ready": True,
        "providers": available,
        "active_provider": llm._current,
    }


@app.get("/stats")
def stats() -> Dict[str, Any]:
    core = get_core()
    if core is None:
        raise HTTPException(status_code=503, detail="Core not initialized")
    if isinstance(core, dict):
        return core["core"].get_stats()
    return core.get_stats()


@app.get("/chain")
def chain() -> Dict[str, Any]:
    core = get_core()
    if core is None:
        raise HTTPException(status_code=503, detail="Core not initialized")
    if isinstance(core, dict):
        return core["ledger"].get_stats()
    return core.ledger.get_stats()


@app.get("/recent")
def recent(limit: int = Query(default=20, ge=1, le=200)) -> List[Dict[str, Any]]:
    core = get_core()
    if core is None:
        raise HTTPException(status_code=503, detail="Core not initialized")
    if isinstance(core, dict):
        return core["core"].history[-limit:][::-1]
    return core.history[-limit:][::-1]


@app.get("/search")
def search(q: str = Query(min_length=2), limit: int = Query(default=10, ge=1, le=50)) -> List[Dict[str, Any]]:
    core = get_core()
    if core is None:
        raise HTTPException(status_code=503, detail="Core not initialized")
    if isinstance(core, dict):
        kg = core["core"].kg
    else:
        kg = core.kg
    return kg.search(q, limit)


@app.post("/cycle")
def trigger_cycle(req: CycleRequest) -> Dict[str, Any]:
    """Trigger a research cycle. Optionally accept a `question` for direct Q&A."""
    core = get_core()
    if core is None:
        raise HTTPException(status_code=503, detail="Core not initialized")
    if isinstance(core, dict):
        c = core["core"]
    else:
        c = core

    if req.question:
        return c.ask_question(req.question, dev_mode=req.dev_mode)

    result = c.run_cycle(dev_mode=req.dev_mode)
    if req.sync_to_hf and result.get("minted"):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "hf_app",
                str(Path(__file__).parent.parent / "hf_deploy" / "app.py"),
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.sync_to_hf_dataset(result)
        except Exception as e:
            result["hf_sync_error"] = str(e)
    return result


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
