"""
Nuclear Intelligence API
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import uvicorn
import gradio as gr

# Fix path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.nuclear_intelligence import NuclearIntelligenceCore
from core.operation_loop import OperationLoop
from blockchain.virtual_ledger import VirtualLedger

app = FastAPI(title="Nuclear Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = {
    "llm_model_large": os.getenv("LLM_MODEL_LARGE", "gpt-4-turbo"),
    "scheduler_interval_minutes": int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "45")),
    "min_accuracy_threshold": 93.0,
    "min_novelty_threshold": 70.0,
    "questions_per_cycle": 3,
}

# Initialize components
ni_core = NuclearIntelligenceCore(config)
virtual_ledger = VirtualLedger(config)
operation_loop = OperationLoop(ni_core, virtual_ledger, config)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting operation loop...")
    asyncio.create_task(operation_loop.run_continuous())

@app.get("/status")
async def get_status():
    return {
        "status": "running",
        "knowledge_base": ni_core.get_knowledge_summary(),
        "blockchain": virtual_ledger.get_chain_state(),
        "operation_loop": operation_loop.get_execution_stats(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/knowledge/records")
async def get_records():
    return virtual_ledger.get_knowledge_records()

@app.post("/api/v1/operations/cycle")
async def trigger_cycle():
    return await operation_loop.execute_cycle()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
