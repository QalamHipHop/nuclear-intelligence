"""
Nuclear Intelligence v3.0 - Enhanced FastAPI
═══════════════════════════════════════════════════════════════════
Secure, rate-limited API with developer mode, monitoring, and analytics
═══════════════════════════════════════════════════════════════════
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import time
import json
from loguru import logger
from collections import defaultdict
from uuid import uuid4

from api.security import RateLimiter as PublicRateLimiter

# Import core components
from core.nuclear_intelligence_v4 import ResearchQuestion
from core.operation_loop import OperationLoop
from core.runtime import RuntimeSettings, build_runtime, runtime_public_status
from core_hf import get_adapter
from core.safety_guard import check_query, render_safe_block

# ─── Initialize FastAPI ───────────────────────────────────────────

app = FastAPI(
    title="Nuclear Intelligence API v3.0",
    description="⚛️ AI-Powered Nuclear Energy Research with Free LLM Providers",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
_cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:7860,http://localhost:8000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# ─── Rate Limiting ────────────────────────────────────────────────

class RateLimiter:
    def __init__(self):
        self.store = defaultdict(list)
        self.blocks = defaultdict(list)

    def check(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        now = datetime.now()
        self.store[key] = [t for t in self.store[key] if now - t < timedelta(seconds=window)]
        remaining = limit - len(self.store[key])
        if remaining <= 0:
            return False, 0
        self.store[key].append(now)
        return True, remaining - 1

    def block_ip(self, ip: str, duration: int = 60):
        self.blocks[ip] = datetime.now() + timedelta(seconds=duration)

    def is_blocked(self, ip: str) -> bool:
        if ip in self.blocks:
            if datetime.now() < self.blocks[ip]:
                return True
            del self.blocks[ip]
        return False

rate_limiter = RateLimiter()
public_rate_limiter = PublicRateLimiter(limit=int(os.getenv("PUBLIC_RATE_LIMIT_PER_MINUTE", "60")), window_seconds=60)


def rate_limit_dependency(req: int = 100, window: int = 60):
    """Rate limiting decorator"""
    def decorator(request: Request, call_next):
        if request.client:
            ip = request.client.host
            if rate_limiter.is_blocked(ip):
                return JSONResponse(status_code=403, content={"detail": "IP blocked"})
            allowed, remaining = rate_limiter.check(ip, req, window)
            if not allowed:
                rate_limiter.block_ip(ip, 60)
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Rate limit exceeded: {req}/{window}s", "retry_after": 60}
                )
        response = call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining) if 'remaining' in dir() else "?"
        return response
    return decorator


# ─── Request Models ────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=2000)
    developer_mode: bool = False
    web_search: bool = True
    category: Optional[str] = None

class CycleRequest(BaseModel):
    developer_mode: bool = False
    force_category: Optional[str] = ""


def require_operator(request: Request) -> None:
    """Protect state-changing and sensitive diagnostics with an operator token."""
    expected = os.getenv("OPERATOR_API_TOKEN", "").strip()
    provided = request.headers.get("X-Operator-Token", "").strip()
    if not expected or not provided or provided != expected:
        raise HTTPException(status_code=403, detail="Operator authorization required")

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    limit: int = Field(default=10, ge=1, le=100)

class TransactionRequest(BaseModel):
    sender: str
    recipient: str
    amount: float = Field(..., gt=0)
    metadata: Optional[Dict] = None


# ─── Global State ──────────────────────────────────────────────────

core = None
ledger = None
op_loop: Optional[OperationLoop] = None
runtime_settings: Optional[RuntimeSettings] = None
adapter = get_adapter()
start_time = datetime.now()


def init_components():
    """Initialize all core components"""
    global core, ledger, op_loop, runtime_settings
    try:
        logger.info("🚀 Initializing API components from canonical runtime...")
        core, op_loop, ledger, runtime_settings = build_runtime()
        logger.info(
            f"✅ API initialized: {len(core.llm._available_providers)} providers, "
            f"{ledger.nes_supply} NES, runtime={runtime_settings.root}"
        )
    except Exception as e:
        logger.error(f"❌ Init error: {e}")


@app.on_event("startup")
async def startup():
    init_components()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Apply bounded public access, request tracing and safe response headers."""
    request_id = request.headers.get("X-Request-ID", "").strip()[:80] or uuid4().hex
    client_key = request.client.host if request.client else "unknown"
    if not public_rate_limiter.allow(client_key):
        return JSONResponse(status_code=429, content={"error": "Request limit reached; retry later.", "request_id": request_id})
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000

    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.0f}ms)")

    if hasattr(response, 'headers'):
        response.headers["X-Response-Time"] = f"{duration:.0f}ms"
        response.headers["X-API-Version"] = "3.0.0"
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"

    return response


# ─── Health & Status Endpoints ────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "Nuclear Intelligence API v3.0",
        "version": "3.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "uptime": str(datetime.now() - start_time),
        "docs": "/docs",
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "uptime_seconds": (datetime.now() - start_time).total_seconds(),
        "components": {
            "core": core is not None,
            "ledger": ledger is not None,
            "op_loop": op_loop is not None,
        },
        "providers": {
            "available": len(core.llm._available_providers) if core else 0,
            "active": core.llm._current_provider if core else None,
        },
        "runtime": runtime_public_status(runtime_settings) if runtime_settings else None,
    }

@app.get("/status")
async def get_status():
    """Get comprehensive system status"""
    if not all([core, ledger, op_loop]):
        raise HTTPException(503, "Components not initialized")

    return {
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "nes_supply": ledger.nes_supply,
            "blocks": len(ledger.chain),
            "entities": len(core.kg.graph.get("entities", {})),
            "total_cycles": len(op_loop.history),
            "loop_running": op_loop.is_running,
        },
        "llm": {
            "providers": core.llm._available_providers,
            "active": core.llm._current_provider,
            "requests": core.llm.get_stats().get("requests", 0),
            "success_rate": core.llm.get_stats().get("success_rate", "N/A"),
        },
        "blockchain": {
            "chain_length": len(ledger.chain),
            "nes_supply": ledger.nes_supply,
            "difficulty": ledger.difficulty,
            "chain_valid": ledger.is_chain_valid(),
        },
    }


# ─── Knowledge Endpoints ───────────────────────────────────────────

@app.post("/api/v1/knowledge/ask")
async def ask_question(request: Request, req: AskRequest):
    """Ask through the canonical safety-checked adapter; public mode is non-developer."""
    result = adapter.ask_question(req.question, developer_mode=False)
    if result.get("error") and not result.get("refused"):
        raise HTTPException(503, result["error"])
    return result


@app.get("/api/v1/knowledge/base")
async def get_knowledge_base():
    """Get knowledge graph stats"""
    if not core:
        raise HTTPException(503, "Core not initialized")

    return {
        "stats": core.kg.get_stats(),
        "categories": core.kg.get_category_stats(),
        "entities_count": len(core.kg.graph.get("entities", {})),
    }


@app.get("/api/v1/knowledge/search")
async def search_knowledge(q: str, limit: int = 10):
    """Search through the canonical knowledge adapter with public bounds."""
    results = adapter.knowledge_search(q, limit)
    if results and results[0].get("error"):
        raise HTTPException(429 if "limit" in results[0]["error"] else 400, results[0]["error"])
    return {"query": q, "results": results, "count": len(results)}


@app.get("/api/v1/knowledge/entity/{entity_id}")
async def get_entity(entity_id: str):
    """Get a specific entity by ID"""
    if not core:
        raise HTTPException(503, "Core not initialized")

    entity = core.kg.graph.get("entities", {}).get(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")

    return entity


@app.get("/api/v1/knowledge/categories")
async def get_categories():
    """Get all categories with counts"""
    if not core:
        raise HTTPException(503, "Core not initialized")

    stats = core.kg.get_category_stats()
    return {
        "categories": [{"name": k, "count": v} for k, v in sorted(stats.items(), key=lambda x: x[1], reverse=True)],
        "total": len(stats),
    }


# ─── Blockchain Endpoints ──────────────────────────────────────────

@app.get("/api/v1/blockchain/state")
async def blockchain_state():
    """Get blockchain state"""
    if not ledger:
        raise HTTPException(503, "Ledger not initialized")

    return ledger.get_stats()


@app.get("/api/v1/blockchain/chain")
async def get_chain():
    """Get full blockchain"""
    if not ledger:
        raise HTTPException(503, "Ledger not initialized")

    return {
        "chain_length": len(ledger.chain),
        "nes_supply": ledger.nes_supply,
        "blocks": [b.to_dict() for b in ledger.chain],
    }


@app.get("/api/v1/blockchain/block/{block_index}")
async def get_block(block_index: int):
    """Get specific block"""
    if not ledger:
        raise HTTPException(503, "Ledger not initialized")

    block_info = ledger.get_block_info(block_index)
    if not block_info:
        raise HTTPException(404, "Block not found")

    return block_info


@app.get("/api/v1/blockchain/balance/{address}")
async def get_balance(address: str):
    """Get address balance"""
    if not ledger:
        raise HTTPException(503, "Ledger not initialized")

    return {
        "address": address,
        "balance": ledger.get_balance(address),
    }


@app.get("/api/v1/blockchain/transactions")
async def get_transactions(
    address: Optional[str] = None,
    tx_type: Optional[str] = None,
    limit: int = 50,
):
    """Get transaction history"""
    if not ledger:
        raise HTTPException(503, "Ledger not initialized")

    return {
        "transactions": ledger.get_transaction_history(address, limit, tx_type),
        "count": len(ledger.chain),
    }


@app.get("/api/v1/blockchain/verify")
async def verify_chain():
    """Verify blockchain integrity"""
    if not ledger:
        raise HTTPException(503, "Ledger not initialized")

    return {
        "is_valid": ledger.is_chain_valid(),
        "blocks": len(ledger.chain),
        "nes_supply": ledger.nes_supply,
        "difficulty": ledger.difficulty,
        "checked_at": datetime.now().isoformat(),
    }


@app.get("/api/v1/blockchain/search")
async def search_transactions(q: str, limit: int = 20):
    """Search transactions"""
    if not ledger:
        raise HTTPException(503, "Ledger not initialized")

    return {
        "query": q,
        "results": ledger.search_transactions(q, limit),
        "count": ledger.total_transactions,
    }


# ─── Operation Endpoints ───────────────────────────────────────────

@app.post("/api/v1/operations/cycle")
async def trigger_cycle(request: Request, req: CycleRequest):
    """Trigger a governed cycle; only an authorized operator may write state."""
    require_operator(request)
    result = adapter.run_cycle(dev_mode=False, public=False)
    if result.get("error"):
        raise HTTPException(503, result["error"])
    return result


@app.post("/api/v1/operations/start")
async def start_loop(request: Request):
    require_operator(request)
    """Start the operation loop"""
    if not op_loop:
        raise HTTPException(503, "Loop not initialized")

    op_loop.start()
    return {"status": "started", "is_running": op_loop.is_running}


@app.post("/api/v1/operations/stop")
async def stop_loop(request: Request):
    require_operator(request)
    """Stop the operation loop"""
    if not op_loop:
        raise HTTPException(503, "Loop not initialized")

    op_loop.stop()
    return {"status": "stopped", "is_running": op_loop.is_running}


@app.post("/api/v1/operations/pause")
async def pause_loop(request: Request):
    require_operator(request)
    """Pause the operation loop"""
    if not op_loop:
        raise HTTPException(503, "Loop not initialized")

    op_loop.pause()
    return {"status": "paused"}


@app.post("/api/v1/operations/resume")
async def resume_loop(request: Request):
    require_operator(request)
    """Resume the operation loop"""
    if not op_loop:
        raise HTTPException(503, "Loop not initialized")

    op_loop.resume()
    return {"status": "resumed", "is_running": op_loop.is_running}


@app.get("/api/v1/operations/stats")
async def op_stats():
    """Get operation loop statistics"""
    if not op_loop:
        raise HTTPException(503, "Loop not initialized")

    return op_loop.get_stats()


@app.get("/api/v1/operations/history")
async def get_history(limit: int = 20):
    """Get cycle history"""
    if not op_loop:
        raise HTTPException(503, "Loop not initialized")

    return {"cycles": op_loop.get_recent_cycles(limit), "total": len(op_loop.history)}


@app.get("/api/v1/operations/best")
async def get_best_cycles(limit: int = 10):
    """Get best performing cycles"""
    if not op_loop:
        raise HTTPException(503, "Loop not initialized")

    return {"cycles": op_loop.get_best_cycles(limit)}


# ─── Developer Endpoints ───────────────────────────────────────────

@app.get("/api/v1/developer/llm-status")
async def llm_status(request: Request):
    require_operator(request)
    """Get detailed LLM provider status"""
    if not core:
        raise HTTPException(503, "Core not initialized")

    return {
        "stats": core.llm.get_stats(),
        "health": core.llm.health_check(),
        "providers": core.llm._available_providers,
    }


@app.get("/api/v1/developer/system-diag")
async def system_diag(request: Request):
    require_operator(request)
    """Get full system diagnostics"""
    if not all([core, ledger, op_loop]):
        raise HTTPException(503, "Components not initialized")

    return {
        "timestamp": datetime.now().isoformat(),
        "uptime": str(datetime.now() - start_time),
        "core_stats": core.get_stats(),
        "ledger_stats": ledger.get_stats(),
        "loop_stats": op_loop.get_stats(),
        "kg_stats": core.kg.get_stats(),
        "llm_stats": core.llm.get_stats(),
        "system_info": {
            "python_version": sys.version,
            "platform": os.getenv("PLATFORM", "unknown"),
        }
    }


@app.get("/api/v1/developer/export-all")
async def export_all(request: Request):
    require_operator(request)
    """Export all data"""
    if not core or not ledger:
        raise HTTPException(503, "Components not initialized")

    return {
        "knowledge_graph": core.kg.export_json(),
        "blockchain": ledger.export_chain(),
        "knowledge_markdown": core.kg.export_markdown(),
    }


# ─── Error Handlers ───────────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": request.headers.get("X-Request-ID", ""),
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.exception_handler(Exception)
async def global_error(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "type": "request_failed",
            "request_id": request.headers.get("X-Request-ID", ""),
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat(),
        }
    )


# ─── Run Server ───────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")