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
    
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block."""
        block_string = json.dumps({
            "block_number": self.block_number,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
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
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "miner": self.miner,
            "hash": self.calculate_hash()
        }


class VirtualLedger:
    """
    Virtual Blockchain Ledger for NES token minting and knowledge recording.
    Provides immutability, transparency, and auditability without external blockchain.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Virtual Ledger."""
        self.config = config
        self.logger = logger
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.balances: Dict[str, float] = {"system": 1000000.0}  # Initial NES supply
        self.transaction_history: List[Dict] = []
        self.merkle_tree: Dict[str, str] = {}
        
        # Initialize genesis block
        self._create_genesis_block()
        
        self.logger.info("Virtual Ledger initialized successfully")
    
    def _create_genesis_block(self) -> None:
        """Create the genesis block."""
        genesis_block = Block(
            block_number=0,
            timestamp=time.time(),
            previous_hash="0" * 64,
            miner="nuclear-intelligence-genesis"
        )
        genesis_block.mine_block()
        self.chain.append(genesis_block)
        self.logger.info(f"Genesis block created: {genesis_block.calculate_hash()}")
    
    def add_transaction(self, tx_type: TransactionType, data: Dict[str, Any],
                       sender: str = "system", receiver: str = "ledger",
                       amount: float = 1.0) -> str:
        """
        Add a new transaction to the pending pool.
        Returns transaction ID.
        """
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
        
        # Sign transaction
        transaction.signature = self._sign_transaction(transaction)
        
        self.pending_transactions.append(transaction)
        self.logger.info(f"Transaction added: {tx_id} ({tx_type.value})")
        
        return tx_id
    
    def mint_nes_token(self, answer_id: str, question: str, answer: str,
                       evaluation_scores: Dict[str, float], answer_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mint 1 NES token for validated scientific knowledge.
        Creates immutable record in blockchain.
        """
        self.logger.info(f"Minting NES token for answer: {answer_id}")
        
        # Prepare token data
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
        
        # Add transaction to pending pool
        tx_id = self.add_transaction(
            tx_type=TransactionType.NES_MINT,
            data=token_data,
            sender="nuclear-intelligence",
            receiver=answer_id,
            amount=1.0
        )
        
        # Update balance
        if answer_id not in self.balances:
            self.balances[answer_id] = 0.0
        self.balances[answer_id] += 1.0
        
        # Record in history
        self.transaction_history.append({
            "tx_id": tx_id,
            "type": "nes_mint",
            "answer_id": answer_id,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        })
        
        return {
            "tx_id": tx_id,
            "token_data": token_data,
            "status": "pending_confirmation",
            "message": f"NES token minting initiated for answer {answer_id}"
        }
    
    def mine_pending_block(self) -> Optional[Block]:
        """
        Mine a new block with all pending transactions.
        Returns the mined block or None if no pending transactions.
        """
        if not self.pending_transactions:
            self.logger.warning("No pending transactions to mine")
            return None
        
        self.logger.info(f"Mining block with {len(self.pending_transactions)} transactions...")
        
        # Create new block
        last_block = self.chain[-1]
        new_block = Block(
            block_number=len(self.chain),
            timestamp=time.time(),
            transactions=self.pending_transactions.copy(),
            previous_hash=last_block.calculate_hash(),
            miner="nuclear-intelligence"
        )
        
        # Mine the block
        new_block.mine_block()
        
        # Add to chain
        self.chain.append(new_block)
        
        # Update transaction history
        for tx in new_block.transactions:
            for hist in self.transaction_history:
                if hist["tx_id"] == tx.tx_id:
                    hist["status"] = "confirmed"
                    hist["block_number"] = new_block.block_number
        
        # Clear pending transactions
        self.pending_transactions = []
        
        self.logger.info(f"Block {new_block.block_number} mined successfully: {new_block.calculate_hash()}")
        
        return new_block
    
    def get_balance(self, address: str) -> float:
        """Get NES token balance for an address."""
        return self.balances.get(address, 0.0)
    
    def get_transaction_history(self, address: Optional[str] = None) -> List[Dict]:
        """Get transaction history, optionally filtered by address."""
        if address is None:
            return self.transaction_history
        
        return [tx for tx in self.transaction_history if tx.get("answer_id") == address]
    
    def get_chain_state(self) -> Dict[str, Any]:
        """Get current state of the blockchain."""
        return {
            "chain_length": len(self.chain),
            "pending_transactions": len(self.pending_transactions),
            "total_nes_minted": sum(self.balances.values()),
            "total_blocks": len(self.chain),
            "last_block_hash": self.chain[-1].calculate_hash() if self.chain else None,
            "timestamp": datetime.now().isoformat()
        }
    
    def verify_chain_integrity(self) -> bool:
        """Verify the integrity of the entire blockchain."""
        self.logger.info("Verifying blockchain integrity...")
        
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Verify hash
            if current_block.calculate_hash() != current_block.calculate_hash():
                self.logger.error(f"Block {i} hash mismatch")
                return False
            
            # Verify previous hash link
            if current_block.previous_hash != previous_block.calculate_hash():
                self.logger.error(f"Block {i} previous hash mismatch")
                return False
        
        self.logger.info("Blockchain integrity verified successfully")
        return True
    
    def export_ledger(self) -> Dict[str, Any]:
        """Export the complete ledger as JSON."""
        return {
            "chain": [block.to_dict() for block in self.chain],
            "balances": self.balances,
            "transaction_history": self.transaction_history,
            "chain_state": self.get_chain_state(),
            "export_timestamp": datetime.now().isoformat()
        }
    
    def _sign_transaction(self, transaction: Transaction) -> str:
        """Sign a transaction (simplified HMAC signature)."""
        message = json.dumps({
            "tx_id": transaction.tx_id,
            "tx_type": transaction.tx_type.value,
            "timestamp": transaction.timestamp,
            "sender": transaction.sender,
            "receiver": transaction.receiver,
            "amount": transaction.amount
        }, sort_keys=True)
        
        secret = self.config.get("blockchain_secret", "nuclear-intelligence-secret")
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def create_merkle_tree(self, transactions: List[Transaction]) -> str:
        """Create Merkle tree for transactions."""
        if not transactions:
            return hashlib.sha256(b"").hexdigest()
        
        # Hash all transactions
        hashes = [
            hashlib.sha256(json.dumps(tx.to_dict()).encode()).hexdigest()
            for tx in transactions
        ]
        
        # Build Merkle tree
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            
            new_hashes = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)
            
            hashes = new_hashes
        
        return hashes[0]
    
    def get_knowledge_records(self) -> List[Dict[str, Any]]:
        """Get all knowledge records (NES minting transactions) from the ledger."""
        records = []
        
        for block in self.chain:
            for tx in block.transactions:
                if tx.tx_type == TransactionType.NES_MINT:
                    records.append({
                        "block_number": block.block_number,
                        "transaction_id": tx.tx_id,
                        "timestamp": tx.timestamp,
                        "data": tx.data,
                        "block_hash": block.calculate_hash()
                    })
        
        return records
