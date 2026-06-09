"""
Enhanced FastAPI Backend for Nuclear Intelligence System.
Provides comprehensive REST API endpoints for system management, monitoring, and external integration.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
import asyncio
from contextlib import asynccontextmanager

from core.nuclear_intelligence_enhanced import NuclearIntelligenceCore, ResearchQuestion
from core.enhanced_operation_loop import EnhancedOperationLoop
from blockchain.enhanced_virtual_ledger import EnhancedVirtualLedger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== Pydantic Models ====================

class QuestionRequest(BaseModel):
    """Request model for generating questions."""
    num_questions: int = 3
    focus_area: Optional[str] = None


class ResearchCycleRequest(BaseModel):
    """Request model for executing a research cycle."""
    execute_immediately: bool = True


class ExternalMintingRequest(BaseModel):
    """Request model for processing external minting."""
    tx_id: str
    external_tx_hash: str


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    status: str
    timestamp: datetime
    cycle_count: int
    successful_mints: int
    chain_state: Dict[str, Any]
    knowledge_summary: Dict[str, Any]


# ==================== Global State ====================

class SystemState:
    """Manages system state and components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ni_core = NuclearIntelligenceCore(config)
        self.operation_loop = EnhancedOperationLoop(config)
        self.ledger = EnhancedVirtualLedger(config)
        self.is_running = False


# Initialize FastAPI app
app = FastAPI(
    title="Nuclear Intelligence API",
    description="Advanced API for autonomous nuclear energy research and knowledge tokenization",
    version="2.0.0"
)

# Global system state
system_state: Optional[SystemState] = None


# ==================== Lifespan Management ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global system_state
    
    # Startup
    logger.info("Initializing Nuclear Intelligence System...")
    config = {
        "llm_model": "gpt-4-turbo",
        "openai_api_key": "your-api-key",
        "blockchain_secret": "nuclear-intelligence-secret",
        "scientific_accuracy_threshold": 93,
        "novelty_threshold": 75,
        "usefulness_threshold": 80,
        "self_consistency_threshold": 90,
        "overall_score_threshold": 85
    }
    system_state = SystemState(config)
    logger.info("System initialized successfully.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nuclear Intelligence System...")
    system_state.is_running = False


app = FastAPI(
    title="Nuclear Intelligence API",
    description="Advanced API for autonomous nuclear energy research and knowledge tokenization",
    version="2.0.0",
    lifespan=lifespan
)


# ==================== Health and Status Endpoints ====================

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Nuclear Intelligence API v2.0"
    }


@app.get("/status")
async def system_status() -> SystemStatusResponse:
    """Get current system status."""
    if not system_state:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return SystemStatusResponse(
        status="running" if system_state.is_running else "idle",
        timestamp=datetime.now(),
        cycle_count=system_state.operation_loop.cycle_count,
        successful_mints=system_state.operation_loop.successful_mints,
        chain_state=system_state.ledger.get_chain_state(),
        knowledge_summary=system_state.ni_core.get_knowledge_summary()
    )


# ==================== Research Endpoints ====================

@app.post("/api/v2/research/questions")
async def generate_questions(request: QuestionRequest) -> Dict[str, Any]:
    """Generate complex research questions."""
    if not system_state:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        questions = await system_state.ni_core.generate_complex_questions(
            num_questions=request.num_questions
        )
        
        return {
            "status": "success",
            "questions_count": len(questions),
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "category": q.category.value,
                    "complexity_level": q.complexity_level,
                    "keywords": q.keywords
                }
                for q in questions
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/research/cycle")
async def execute_research_cycle(
    request: ResearchCycleRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Execute a complete research cycle."""
    if not system_state:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        if request.execute_immediately:
            cycle_result = await system_state.operation_loop.execute_research_cycle()
            return {
                "status": "completed",
                "cycle_result": cycle_result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            background_tasks.add_task(
                system_state.operation_loop.execute_research_cycle
            )
            return {
                "status": "queued",
                "message": "Research cycle queued for background execution",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error executing research cycle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Blockchain Endpoints ====================

@app.get("/api/v2/blockchain/state")
async def get_blockchain_state() -> Dict[str, Any]:
    """Get current blockchain state."""
    if not system_state:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return {
        "status": "success",
        "chain_state": system_state.ledger.get_chain_state(),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v2/blockchain/knowledge-records")
async def get_knowledge_records() -> Dict[str, Any]:
    """Get all knowledge records (NES minting transactions)."""
    if not system_state:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    records = system_state.ledger.get_knowledge_records()
    
    return {
        "status": "success",
        "records_count": len(records),
        "records": records,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v2/blockchain/export")
async def export_ledger() -> Dict[str, Any]:
    """Export complete ledger state."""
    if not system_state:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return system_state.ledger.export_ledger()


@app.get("/api/v2/blockchain/balance/{address}")
async def get_nes_balance(address: str) -> Dict[str, Any]:
    """Get NES token balance for an address."""
    if not system_state:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    balance = system_state.ledger.get_nes_balance(address)
    
    return {
        "status": "success",
        "address": address,
        "balance": balance,
        "timestamp": datetime.now().isoformat()
    }


# ==================== External Integration Endpoints ====================

@app.get("/api/v2/external/minting-queue")
async def get_external_minting_queue() -> Dict[str, Any]:
    """Get queue of transactions pending external minting."""
    if not system_state:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    queue = system_state.ledger.get_external_minting_queue()
    
    return {
        "status": "success",
        "queue_size": len(queue),
        "queue": queue,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v2/external/process-minting")
async def process_external_minting(request: ExternalMintingRequest) -> Dict[str, Any]:
    """Process external minting confirmation."""
    if not system_state:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        success = system_state.ledger.process_external_minting(
            tx_id=request.tx_id,
            external_tx_hash=request.external_tx_hash
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Transaction {request.tx_id} marked as externally minted",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction {request.tx_id} not found in minting queue"
            )
    except Exception as e:
        logger.error(f"Error processing external minting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Knowledge Base Endpoints ====================

@app.get("/api/v2/knowledge/summary")
async def get_knowledge_summary() -> Dict[str, Any]:
    """Get knowledge base summary."""
    if not system_state:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    summary = system_state.ni_core.get_knowledge_summary()
    
    return {
        "status": "success",
        "summary": summary,
        "timestamp": datetime.now().isoformat()
    }


# ==================== Statistics Endpoints ====================

@app.get("/api/v2/statistics/operations")
async def get_operation_statistics() -> Dict[str, Any]:
    """Get operation loop statistics."""
    if not system_state:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    stats = system_state.operation_loop.get_operation_statistics()
    
    return {
        "status": "success",
        "statistics": stats,
        "timestamp": datetime.now().isoformat()
    }


# ==================== Main Execution ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
