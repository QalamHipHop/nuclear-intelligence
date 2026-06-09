"""
Nuclear Intelligence API
FastAPI application for managing the Nuclear Intelligence system.
Provides endpoints for knowledge queries, blockchain state, and system management.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger
import uvicorn

# Import core modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.nuclear_intelligence import NuclearIntelligenceCore, ResearchQuestion
from core.operation_loop import OperationLoop
from blockchain.virtual_ledger import VirtualLedger


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Models for API
# ─────────────────────────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    """Request model for asking a question."""
    question: str
    category: Optional[str] = "ai_integration"
    keywords: Optional[List[str]] = []


class KnowledgeResponse(BaseModel):
    """Response model for knowledge queries."""
    question: str
    answer: str
    sources: List[Dict[str, str]]
    confidence: float
    timestamp: str


class BlockchainStateResponse(BaseModel):
    """Response model for blockchain state."""
    chain_length: int
    pending_transactions: int
    total_nes_minted: float
    last_block_hash: str
    timestamp: str


class SystemStatsResponse(BaseModel):
    """Response model for system statistics."""
    total_cycles: int
    successful_cycles: int
    failed_cycles: int
    total_questions_generated: int
    total_answers_generated: int
    total_tokens_minted: int
    average_accuracy: float
    last_cycle_time: Optional[str]


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Application Setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Nuclear Intelligence API",
    description="AI-powered nuclear energy research and NES token system",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Global State
# ─────────────────────────────────────────────────────────────────────────────

config = {
    "llm_model_large": os.getenv("LLM_MODEL_LARGE", "gpt-4-turbo"),
    "llm_model_medium": os.getenv("LLM_MODEL_MEDIUM", "gpt-3.5-turbo"),
    "scheduler_interval_minutes": int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "45")),
    "min_accuracy_threshold": 93.0,
    "min_novelty_threshold": 70.0,
    "questions_per_cycle": 3,
    "feature_human_in_the_loop": os.getenv("FEATURE_HUMAN_IN_THE_LOOP", "true").lower() == "true",
    "blockchain_secret": os.getenv("BLOCKCHAIN_SECRET", "nuclear-intelligence-secret")
}

# Initialize core components
ni_core = NuclearIntelligenceCore(config)
virtual_ledger = VirtualLedger(config)
operation_loop = OperationLoop(ni_core, virtual_ledger, config)

# Background task for continuous operation loop
operation_loop_task = None


# ─────────────────────────────────────────────────────────────────────────────
# Startup and Shutdown Events
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    logger.info("Nuclear Intelligence API starting up...")
    logger.info(f"Configuration: {config}")
    
    # Start operation loop in background
    global operation_loop_task
    operation_loop_task = asyncio.create_task(
        operation_loop.run_continuous(max_cycles=None)
    )
    logger.info("Operation loop started in background")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Nuclear Intelligence API shutting down...")
    
    if operation_loop_task:
        operation_loop_task.cancel()
    
    logger.info("Shutdown complete")


# ─────────────────────────────────────────────────────────────────────────────
# Health and Status Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Nuclear Intelligence API",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/status")
async def system_status() -> Dict[str, Any]:
    """Get system status."""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "knowledge_base": ni_core.get_knowledge_summary(),
        "blockchain": virtual_ledger.get_chain_state(),
        "operation_loop": operation_loop.get_execution_stats()
    }


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v1/knowledge/ask")
async def ask_question(request: QuestionRequest) -> KnowledgeResponse:
    """
    Ask a question and get an answer from the knowledge base.
    """
    logger.info(f"Received question: {request.question[:100]}")
    
    try:
        # Search knowledge base
        # This would integrate with the RAG system
        
        return KnowledgeResponse(
            question=request.question,
            answer="Answer from knowledge base...",
            sources=[],
            confidence=0.85,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/knowledge/base")
async def get_knowledge_base() -> Dict[str, Any]:
    """Get the current knowledge base."""
    return {
        "summary": ni_core.get_knowledge_summary(),
        "total_entries": len(ni_core.knowledge_base),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/knowledge/records")
async def get_knowledge_records() -> List[Dict[str, Any]]:
    """Get all knowledge records from the blockchain."""
    records = virtual_ledger.get_knowledge_records()
    return records


# ─────────────────────────────────────────────────────────────────────────────
# Blockchain Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/blockchain/state")
async def get_blockchain_state() -> BlockchainStateResponse:
    """Get current blockchain state."""
    state = virtual_ledger.get_chain_state()
    
    return BlockchainStateResponse(
        chain_length=state["chain_length"],
        pending_transactions=state["pending_transactions"],
        total_nes_minted=state["total_nes_minted"],
        last_block_hash=state["last_block_hash"] or "genesis",
        timestamp=state["timestamp"]
    )


@app.get("/api/v1/blockchain/chain")
async def get_blockchain() -> Dict[str, Any]:
    """Get the complete blockchain."""
    ledger_export = virtual_ledger.export_ledger()
    return ledger_export


@app.get("/api/v1/blockchain/balance/{address}")
async def get_balance(address: str) -> Dict[str, Any]:
    """Get NES token balance for an address."""
    balance = virtual_ledger.get_balance(address)
    
    return {
        "address": address,
        "balance": balance,
        "currency": "NES",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/blockchain/transactions/{address}")
async def get_transactions(address: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get transaction history."""
    transactions = virtual_ledger.get_transaction_history(address)
    return transactions


@app.post("/api/v1/blockchain/mine")
async def mine_block() -> Dict[str, Any]:
    """Manually trigger block mining."""
    try:
        block = virtual_ledger.mine_pending_block()
        
        if block:
            return {
                "status": "success",
                "block_number": block.block_number,
                "hash": block.calculate_hash(),
                "transactions": len(block.transactions),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "no_pending_transactions",
                "message": "No pending transactions to mine"
            }
    except Exception as e:
        logger.error(f"Error mining block: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Operation Loop Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/operations/stats")
async def get_operation_stats() -> SystemStatsResponse:
    """Get operation loop statistics."""
    stats = operation_loop.get_execution_stats()
    
    return SystemStatsResponse(
        total_cycles=stats["total_cycles"],
        successful_cycles=stats["successful_cycles"],
        failed_cycles=stats["failed_cycles"],
        total_questions_generated=stats["total_questions_generated"],
        total_answers_generated=stats["total_answers_generated"],
        total_tokens_minted=stats["total_tokens_minted"],
        average_accuracy=stats["average_accuracy"],
        last_cycle_time=stats.get("last_cycle_time")
    )


@app.post("/api/v1/operations/cycle")
async def execute_operation_cycle(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Manually trigger an operation cycle."""
    try:
        cycle_report = await operation_loop.execute_cycle()
        
        return {
            "status": "success",
            "cycle_number": cycle_report["cycle_number"],
            "questions_generated": len(cycle_report["questions"]),
            "answers_generated": len(cycle_report["answers"]),
            "tokens_minted": len(cycle_report["tokens_minted"]),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing operation cycle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/operations/cycles")
async def get_cycle_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent operation cycle history."""
    return operation_loop.cycle_history[-limit:]


# ─────────────────────────────────────────────────────────────────────────────
# System Management Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v1/system/verify-integrity")
async def verify_system_integrity() -> Dict[str, Any]:
    """Verify system integrity."""
    blockchain_ok = virtual_ledger.verify_chain_integrity()
    
    return {
        "blockchain_integrity": blockchain_ok,
        "knowledge_base_size": len(ni_core.knowledge_base),
        "pending_transactions": len(virtual_ledger.pending_transactions),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/system/config")
async def get_system_config() -> Dict[str, Any]:
    """Get system configuration (non-sensitive)."""
    return {
        "llm_model_large": config["llm_model_large"],
        "llm_model_medium": config["llm_model_medium"],
        "scheduler_interval_minutes": config["scheduler_interval_minutes"],
        "min_accuracy_threshold": config["min_accuracy_threshold"],
        "min_novelty_threshold": config["min_novelty_threshold"],
        "questions_per_cycle": config["questions_per_cycle"],
        "feature_human_in_the_loop": config["feature_human_in_the_loop"]
    }


@app.get("/api/v1/system/export")
async def export_system_state() -> Dict[str, Any]:
    """Export complete system state."""
    return {
        "timestamp": datetime.now().isoformat(),
        "blockchain": virtual_ledger.export_ledger(),
        "knowledge_base": {
            "summary": ni_core.get_knowledge_summary(),
            "entries": len(ni_core.knowledge_base)
        },
        "operation_stats": operation_loop.get_execution_stats()
    }


# ─────────────────────────────────────────────────────────────────────────────
# Root Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "name": "Nuclear Intelligence API",
        "version": "0.1.0",
        "description": "AI-powered nuclear energy research and NES token system",
        "docs": "/docs",
        "status_endpoint": "/status"
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("API_DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting Nuclear Intelligence API on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
