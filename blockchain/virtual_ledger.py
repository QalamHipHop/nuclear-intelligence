"""
Virtual Blockchain Ledger Module
Implements an internal blockchain simulation for NES token minting with full immutability,
transparency, and auditability features.
"""
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import hmac
from loguru import logger
from pydantic import BaseModel, Field

class TransactionType(str, Enum):
    """Types of transactions in the ledger."""
    NES_MINT = "nes_mint"
    KNOWLEDGE_RECORD = "knowledge_record"
    TRANSFER = "transfer"
    GOVERNANCE = "governance"

@dataclass
class Transaction:
    """Represents a single transaction in the blockchain."""
    tx_id: str
    tx_type: TransactionType
    timestamp: float
    data: Dict[str, Any]
    sender: str = "system"
    receiver: str = "ledger"
    amount: float = 1.0  # NES tokens
    nonce: int = 0
    signature: str = ""

    def to_dict(self) -> Dict:
        """Convert transaction to dictionary."""
        return {
            "tx_id": self.tx_id,
            "tx_type": self.tx_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "nonce": self.nonce,
            "signature": self.signature
        }

@dataclass
class Block:
    """Represents a block in the virtual blockchain."""
    block_number: int
    timestamp: float
    transactions: List[Transaction] = field(default_factory=list)
    previous_hash: str = "0" * 64
    nonce: int = 0
    miner: str = "nuclear-intelligence"
    difficulty: int = 2
    merkle_root: str = ""

    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block."""
        block_string = json.dumps({
            "block_number": self.block_number,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "miner": self.miner
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self) -> None:
        """Mine the block with proof-of-work."""
        target = "0" * self.difficulty
        while self.calculate_hash()[:self.difficulty] != target:
            self.nonce += 1

    def to_dict(self) -> Dict:
        """Convert block to dictionary."""
        return {
            "block_number": self.block_number,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "merkle_root": self.merkle_root,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "miner": self.miner,
            "hash": self.calculate_hash()
        }

class VirtualLedger:
    """
    Virtual Blockchain Ledger for NES token minting and knowledge recording.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logger
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.balances: Dict[str, float] = {"system": 1000000.0}
        self.transaction_history: List[Dict] = []
        self._create_genesis_block()
        self.logger.info("Virtual Ledger initialized successfully")

    def _create_genesis_block(self) -> None:
        """Create the genesis block."""
        genesis_block = Block(
            block_number=0,
            timestamp=time.time(),
            previous_hash="0" * 64,
            miner="nuclear-intelligence-genesis",
            merkle_root=hashlib.sha256(b"genesis").hexdigest()
        )
        genesis_block.mine_block()
        self.chain.append(genesis_block)
        self.logger.info(f"Genesis block created: {genesis_block.calculate_hash()}")

    def add_transaction(self, tx_type: TransactionType, data: Dict[str, Any],
                       sender: str = "system", receiver: str = "ledger",
                       amount: float = 1.0) -> str:
        """Add a new transaction to the pending pool."""
        tx_id = hashlib.sha256(
            f"{sender}{receiver}{time.time()}{json.dumps(data)}".encode()
        ).hexdigest()[:16]
        transaction = Transaction(
            tx_id=tx_id,
            tx_type=tx_type,
            timestamp=time.time(),
            data=data,
            sender=sender,
            receiver=receiver,
            amount=amount,
            nonce=len(self.pending_transactions)
        )
        transaction.signature = self._sign_transaction(transaction)
        self.pending_transactions.append(transaction)
        self.logger.info(f"Transaction added: {tx_id} ({tx_type.value})")
        return tx_id

    def mint_nes_token(self, answer_id: str, question: str, answer: str,
                       evaluation_scores: Dict[str, float], answer_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Mint 1 NES token for validated scientific knowledge."""
        token_data = {
            "token_type": "NES",
            "token_symbol": "NES",
            "token_value": 1.0,
            "answer_id": answer_id,
            "question": question[:500],
            "answer_hash": hashlib.sha256(answer.encode()).hexdigest(),
            "evaluation_scores": evaluation_scores,
            "metadata": answer_metadata,
            "timestamp": datetime.now().isoformat(),
            "model_version": self.config.get("llm_model_large", "gpt-4-turbo"),
            "hf_link": f"https://huggingface.co/spaces/Qalam/Nuclear-Intelligence"
        }
        tx_id = self.add_transaction(
            tx_type=TransactionType.NES_MINT,
            data=token_data,
            sender="nuclear-intelligence",
            receiver=answer_id,
            amount=1.0
        )
        if answer_id not in self.balances:
            self.balances[answer_id] = 0.0
        self.balances[answer_id] += 1.0
        self.transaction_history.append({
            "tx_id": tx_id,
            "type": "nes_mint",
            "answer_id": answer_id,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        })
        return {"tx_id": tx_id, "token_data": token_data, "status": "pending_confirmation"}

    def create_merkle_tree(self, transactions: List[Transaction]) -> str:
        """Create Merkle tree root for transactions."""
        if not transactions:
            return hashlib.sha256(b"").hexdigest()
        hashes = [hashlib.sha256(json.dumps(tx.to_dict()).encode()).hexdigest() for tx in transactions]
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            new_hashes = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            hashes = new_hashes
        return hashes[0]

    def mine_pending_block(self) -> Optional[Block]:
        """Mine a new block with all pending transactions."""
        if not self.pending_transactions:
            return None
        last_block = self.chain[-1]
        new_block = Block(
            block_number=len(self.chain),
            timestamp=time.time(),
            transactions=self.pending_transactions.copy(),
            previous_hash=last_block.calculate_hash(),
            miner="nuclear-intelligence",
            merkle_root=self.create_merkle_tree(self.pending_transactions)
        )
        new_block.mine_block()
        self.chain.append(new_block)
        for tx in new_block.transactions:
            for hist in self.transaction_history:
                if hist["tx_id"] == tx.tx_id:
                    hist["status"] = "confirmed"
                    hist["block_number"] = new_block.block_number
        self.pending_transactions = []
        return new_block

    def get_chain_state(self) -> Dict[str, Any]:
        return {
            "chain_length": len(self.chain),
            "total_nes_minted": sum(self.balances.values()) - 1000000.0,
            "last_block_hash": self.chain[-1].calculate_hash() if self.chain else None,
            "timestamp": datetime.now().isoformat()
        }

    def _sign_transaction(self, transaction: Transaction) -> str:
        message = json.dumps(transaction.to_dict(), sort_keys=True)
        secret = self.config.get("blockchain_secret", "nuclear-intelligence-secret")
        return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

    def get_knowledge_records(self) -> List[Dict[str, Any]]:
        records = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.tx_type == TransactionType.NES_MINT:
                    records.append({"block": block.block_number, "tx": tx.tx_id, "data": tx.data})
        return records

    def export_ledger(self) -> Dict[str, Any]:
        return {
            "chain": [block.to_dict() for block in self.chain],
            "balances": self.balances,
            "transaction_history": self.transaction_history,
            "export_timestamp": datetime.now().isoformat()
        }
