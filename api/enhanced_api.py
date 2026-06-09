
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from core.nuclear_intelligence import NuclearIntelligenceCore
from blockchain.virtual_ledger import VirtualLedger
from core.operation_loop import OperationLoop
import uvicorn

app = FastAPI(title="Nuclear Intelligence API", version="1.0.0")

# Shared components (initialized in main)
core = None
ledger = None
op_loop = None

def init_components(c, l, o):
    global core, ledger, op_loop
    core = c
    ledger = l
    op_loop = o

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/blockchain/state")
def get_blockchain():
    return [block.to_dict() for block in ledger.chain]

@app.get("/blockchain/balance/{address}")
def get_balance(address: str):
    return {"address": address, "balance": ledger.get_balance(address)}

@app.get("/knowledge/graph")
def get_kg():
    return core.kg.graph

@app.post("/operations/cycle")
def trigger_cycle():
    try:
        result = op_loop.run_cycle()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/operations/stats")
def get_stats():
    return {
        "nes_supply": ledger.nes_supply,
        "blocks": len(ledger.chain),
        "entities": len(core.kg.graph["entities"]),
        "history_count": len(op_loop.history)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
