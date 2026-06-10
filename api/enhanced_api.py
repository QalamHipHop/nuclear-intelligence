
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

@app.get("/status")
def get_status():
    return {
        "status": "active",
        "nes_supply": ledger.nes_supply if ledger else 0,
        "blocks": len(ledger.chain) if ledger else 0,
        "loop_running": op_loop.is_running if op_loop else False
    }

@app.get("/api/v1/blockchain/state")
def get_blockchain():
    if not ledger: raise HTTPException(status_code=503, detail="Ledger not initialized")
    return [block.to_dict() for block in ledger.chain]

@app.get("/api/v1/blockchain/balance/{address}")
def get_balance(address: str):
    if not ledger: raise HTTPException(status_code=503, detail="Ledger not initialized")
    return {"address": address, "balance": ledger.get_balance(address)}

@app.get("/api/v1/knowledge/base")
def get_kg():
    if not core: raise HTTPException(status_code=503, detail="Core not initialized")
    return core.kg.graph

@app.post("/api/v1/operations/cycle")
def trigger_cycle():
    if not op_loop: raise HTTPException(status_code=503, detail="Operation loop not initialized")
    try:
        result = op_loop.run_cycle()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/operations/stats")
def get_stats():
    if not (ledger and core and op_loop): raise HTTPException(status_code=503, detail="System not fully initialized")
    return {
        "nes_supply": ledger.nes_supply,
        "blocks": len(ledger.chain),
        "entities": len(core.kg.graph["entities"]),
        "history_count": len(op_loop.history)
    }

@app.get("/api/v1/blockchain/chain")
def get_full_chain():
    if not ledger: raise HTTPException(status_code=503, detail="Ledger not initialized")
    return [block.to_dict() for block in ledger.chain]

@app.post("/api/v1/blockchain/mine")
def manual_mine():
    if not ledger: raise HTTPException(status_code=503, detail="Ledger not initialized")
    block = ledger.mine_pending_transactions()
    if block:
        return block.to_dict()
    return {"message": "No pending transactions to mine"}

@app.get("/api/v1/operations/cycles")
def get_cycle_history():
    if not op_loop: raise HTTPException(status_code=503, detail="Operation loop not initialized")
    return op_loop.history

@app.post("/api/v1/system/verify-integrity")
def verify_integrity():
    if not ledger: raise HTTPException(status_code=503, detail="Ledger not initialized")
    is_valid = ledger.is_chain_valid()
    return {"is_valid": is_valid}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
