"""Nuclear Intelligence - Enhanced FastAPI v2.0
Secure, rate-limited with developer mode and monitoring"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import time, json
from loguru import logger

from core.nuclear_intelligence import NuclearIntelligenceCore
from core.operation_loop import OperationLoop, OperationLoopConfig
from blockchain.virtual_ledger import VirtualLedger

app = FastAPI(title="Nuclear Intelligence API v2.0", description="AI-powered nuclear research with free LLM providers", version="2.0.0")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Rate limiting
from collections import defaultdict
from datetime import datetime, timedelta
rate_store = defaultdict(list)

def rate_limit(req: int = 100, window: int = 60):
    def decorator(request: Request, call_next):
        key = f"{request.client.host if request.client else 'unknown'}:{int(time.time() // window)}"
        now = datetime.now()
        rate_store[key] = [t for t in rate_store[key] if now - t < timedelta(seconds=window)]
        if len(rate_store[key]) >= req: return JSONResponse(status_code=429, content={"detail": f"Rate limit: {req}/{window}s"})
        rate_store[key].append(now)
        return call_next(request)
    return decorator

class AskRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=1000)
    developer_mode: bool = False
    web_search: bool = True

class CycleRequest(BaseModel):
    developer_mode: bool = False

core: Optional[NuclearIntelligenceCore] = None
ledger: Optional[VirtualLedger] = None
op_loop: Optional[OperationLoop] = None

def init_components():
    global core, ledger, op_loop
    try:
        core = NuclearIntelligenceCore()
        ledger = VirtualLedger()
        config = OperationLoopConfig(interval_minutes=int(os.getenv("OPERATION_LOOP_INTERVAL_MINUTES", 30)), min_accuracy=float(os.getenv("SCIENTIFIC_ACCURACY_THRESHOLD", 93.0)), developer_mode=os.getenv("DEVELOPER_MODE","false").lower()=="true")
        op_loop = OperationLoop(core, ledger, config=config)
        logger.info("API components initialized")
    except Exception as e:
        logger.error(f"Init error: {e}")

@app.on_event("startup")
async def startup(): init_components()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({(time.time()-start)*1000:.0f}ms)")
    return response

@app.get("/health")
async def health(): return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "2.0.0", "core_available": core is not None}

@app.get("/status")
async def get_status():
    if not all([core, ledger, op_loop]): raise HTTPException(503, "Components not initialized")
    return {"status": "active", "nes_supply": ledger.nes_supply, "blocks": len(ledger.chain), "entities": len(core.kg.graph["entities"]), "loop_running": op_loop.is_running, "llm_provider": core.llm._current_provider, "llm_providers": core.llm._available_providers}

@app.post("/api/v1/knowledge/ask")
@rate_limit(30, 60)
async def ask_question(req: AskRequest):
    if not core: raise HTTPException(503, "Core not initialized")
    try:
        from core.nuclear_intelligence import ResearchQuestion
        q = ResearchQuestion(question=req.question, category="User Query", difficulty=5, keywords=[])
        answer = core.conduct_research(q, use_web_search=req.web_search)
        evaluation = core.evaluate_answer(q, answer)
        result = {"question": req.question, "answer": answer.answer, "citations": answer.citations, "evaluation": evaluation.to_dict(), "llm_provider": core.llm._current_provider, "timestamp": datetime.now().isoformat()}
        if req.developer_mode: result["developer_analysis"] = core.developer_mode_analysis(q, answer)
        return result
    except Exception as e:
        logger.error(f"Ask error: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/v1/knowledge/base")
async def get_knowledge_base():
    if not core: raise HTTPException(503, "Core not initialized")
    return {"stats": core.kg.get_stats(), "categories": core.kg.get_category_stats()}

@app.get("/api/v1/knowledge/search")
async def search_knowledge(q: str, limit: int = 10):
    if not core: raise HTTPException(503, "Core not initialized")
    return {"query": q, "results": core.kg.search_entities(q, limit=limit), "count": len(core.kg.graph["entities"])}

@app.get("/api/v1/blockchain/state")
async def blockchain_state():
    if not ledger: raise HTTPException(503, "Ledger not initialized")
    return ledger.get_stats()

@app.get("/api/v1/blockchain/chain")
async def get_chain():
    if not ledger: raise HTTPException(503, "Ledger not initialized")
    return {"chain_length": len(ledger.chain), "nes_supply": ledger.nes_supply, "blocks": [b.to_dict() for b in ledger.chain]}

@app.get("/api/v1/blockchain/balance/{address}")
async def get_balance(address: str):
    if not ledger: raise HTTPException(503, "Ledger not initialized")
    return {"address": address, "balance": ledger.get_balance(address)}

@app.get("/api/v1/blockchain/verify")
async def verify_chain():
    if not ledger: raise HTTPException(503, "Ledger not initialized")
    return {"is_valid": ledger.is_chain_valid(), "blocks": len(ledger.chain), "checked_at": datetime.now().isoformat()}

@app.post("/api/v1/operations/cycle")
@rate_limit(5, 60)
async def trigger_cycle(req: CycleRequest):
    if not op_loop: raise HTTPException(503, "Loop not initialized")
    try: result = op_loop.run_cycle(developer_mode=req.developer_mode); return result.to_dict()
    except Exception as e: raise HTTPException(500, str(e))

@app.post("/api/v1/operations/start")
async def start_loop():
    if not op_loop: raise HTTPException(503, "Loop not initialized")
    op_loop.start(); return {"status": "started", "is_running": op_loop.is_running}

@app.post("/api/v1/operations/stop")
async def stop_loop():
    if not op_loop: raise HTTPException(503, "Loop not initialized")
    op_loop.stop(); return {"status": "stopped", "is_running": op_loop.is_running}

@app.get("/api/v1/operations/stats")
async def op_stats():
    if not op_loop: raise HTTPException(503, "Loop not initialized")
    return op_loop.get_stats()

@app.get("/api/v1/developer/llm-status")
async def llm_status():
    if not core: raise HTTPException(503, "Core not initialized")
    return {"stats": core.llm.get_stats(), "health": core.llm.health_check()}

@app.get("/api/v1/developer/system-diag")
async def system_diag():
    if not all([core, ledger, op_loop]): raise HTTPException(503, "Components not initialized")
    return {"timestamp": datetime.now().isoformat(), "core_stats": core.get_stats(), "ledger_stats": ledger.get_stats(), "loop_stats": op_loop.get_stats(), "kg_stats": core.kg.get_stats(), "llm_stats": core.llm.get_stats()}

@app.get("/api/v1/developer/export-all")
async def export_all():
    if not core or not ledger: raise HTTPException(503, "Components not initialized")
    return {"knowledge_graph": core.kg.export_json(), "blockchain": ledger.export_chain(), "knowledge_markdown": core.kg.export_markdown()}

@app.exception_handler(Exception)
async def global_error(request: Request, exc: Exception):
    logger.error(f"Error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal error", "path": str(request.url.path)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_PORT", 8000)))
