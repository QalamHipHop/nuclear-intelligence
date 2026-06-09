"""
Enhanced Virtual Ledger with Full Blockchain Features, NES Token Minting,
and Integration with External Blockchain Networks.
"""

import hashlib
import hmac
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Data Models ====================

class TransactionType(str, Enum):
    """Types of transactions in the blockchain."""
    KNOWLEDGE_RECORD = "knowledge_record"
    NES_MINT = "nes_mint"
    NES_TRANSFER = "nes_transfer"
    SYSTEM_EVENT = "system_event"


@dataclass
class Transaction:
    """Represents a blockchain transaction."""
    tx_id: str
    tx_type: TransactionType
    timestamp: float
    data: Dict[str, Any]
    sender: str
    receiver: str
    amount: float
    nonce: int
    signature: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
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
    """Represents a block in the blockchain."""
    block_number: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    miner: str
    merkle_root: str
    nonce: int = 0
    difficulty: int = 4
    
    def calculate_hash(self) -> str:
        """Calculate the SHA-256 hash of the block."""
        block_data = {
            "block_number": self.block_number,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "miner": self.miner,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int = None):
        """Mine the block using Proof of Work."""
        if difficulty:
            self.difficulty = difficulty
        
        target = "0" * self.difficulty
        current_hash = self.calculate_hash()
        
        while not current_hash.startswith(target):
            self.nonce += 1
            current_hash = self.calculate_hash()
        
        logger.info(f"Block {self.block_number} mined with nonce {self.nonce}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_number": self.block_number,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "miner": self.miner,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "hash": self.calculate_hash()
        }


# ==================== Enhanced Virtual Ledger ====================

class EnhancedVirtualLedger:
    """Enhanced Virtual Ledger with full blockchain features and NES token integration."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.balances: Dict[str, float] = {"nuclear-intelligence": 1000000.0}
        self.transaction_history: List[Dict[str, Any]] = []
        self.logger = logger
        
        # Initialize genesis block
        self._create_genesis_block()
        
        # External blockchain integration
        self.external_network_config = config.get("external_network", {})
        self.external_minting_queue: List[Dict[str, Any]] = []
    
    def _create_genesis_block(self):
        """Create the genesis block."""
        genesis_block = Block(
            block_number=0,
            timestamp=time.time(),
            transactions=[],
            previous_hash="0",
            miner="genesis",
            merkle_root=hashlib.sha256(b"").hexdigest()
        )
        genesis_block.mine_block(difficulty=2)
        self.chain.append(genesis_block)
        self.logger.info("Genesis block created.")
    
    def add_transaction(self, tx_type: TransactionType, data: Dict[str, Any],
                       sender: str, receiver: str, amount: float = 0.0) -> str:
        """Add a transaction to the pending transactions pool."""
        tx_id = hashlib.md5(f"{sender}{receiver}{time.time()}".encode()).hexdigest()[:16]
        
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
            "answer_length": len(answer),
            "evaluation_scores": evaluation_scores,
            "metadata": answer_metadata,
            "timestamp": datetime.now().isoformat(),
            "model_version": self.config.get("llm_model_large", "gpt-4-turbo"),
            "hf_link": f"https://huggingface.co/spaces/Qalam/Nuclear-Intelligence",
            "security_hash": hashlib.sha256(
                json.dumps(evaluation_scores, sort_keys=True).encode()
            ).hexdigest()
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
            "status": "pending",
            "token_data": token_data
        })
        
        # Queue for external minting
        self.external_minting_queue.append({
            "tx_id": tx_id,
            "token_data": token_data,
            "status": "pending_external_mint"
        })
        
        return {
            "tx_id": tx_id,
            "token_data": token_data,
            "status": "pending_confirmation",
            "external_queue_position": len(self.external_minting_queue)
        }
    
    def create_merkle_tree(self, transactions: List[Transaction]) -> str:
        """Create Merkle tree root for transactions."""
        if not transactions:
            return hashlib.sha256(b"").hexdigest()
        
        hashes = [
            hashlib.sha256(json.dumps(tx.to_dict()).encode()).hexdigest()
            for tx in transactions
        ]
        
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            
            new_hashes = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            
            hashes = new_hashes
        
        return hashes[0]
    
    def mine_pending_block(self, difficulty: int = 4) -> Optional[Block]:
        """Mine a new block with all pending transactions."""
        if not self.pending_transactions:
            self.logger.warning("No pending transactions to mine.")
            return None
        
        last_block = self.chain[-1]
        new_block = Block(
            block_number=len(self.chain),
            timestamp=time.time(),
            transactions=self.pending_transactions.copy(),
            previous_hash=last_block.calculate_hash(),
            miner="nuclear-intelligence",
            merkle_root=self.create_merkle_tree(self.pending_transactions),
            difficulty=difficulty
        )
        
        new_block.mine_block()
        self.chain.append(new_block)
        
        # Update transaction history
        for tx in new_block.transactions:
            for hist in self.transaction_history:
                if hist["tx_id"] == tx.tx_id:
                    hist["status"] = "confirmed"
                    hist["block_number"] = new_block.block_number
                    hist["block_hash"] = new_block.calculate_hash()
        
        self.pending_transactions = []
        self.logger.info(f"Block {new_block.block_number} mined successfully.")
        
        return new_block
    
    def verify_chain_integrity(self) -> bool:
        """Verify the integrity of the entire blockchain."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Verify hash chain
            if current_block.previous_hash != previous_block.calculate_hash():
                self.logger.error(f"Hash mismatch at block {i}")
                return False
            
            # Verify Merkle root
            calculated_merkle = self.create_merkle_tree(current_block.transactions)
            if current_block.merkle_root != calculated_merkle:
                self.logger.error(f"Merkle root mismatch at block {i}")
                return False
        
        self.logger.info("Blockchain integrity verified.")
        return True
    
    def get_chain_state(self) -> Dict[str, Any]:
        """Get the current state of the blockchain."""
        return {
            "chain_length": len(self.chain),
            "total_nes_minted": sum(self.balances.values()) - 1000000.0,
            "pending_transactions": len(self.pending_transactions),
            "last_block_hash": self.chain[-1].calculate_hash() if self.chain else None,
            "last_block_number": len(self.chain) - 1,
            "total_transactions": sum(len(block.transactions) for block in self.chain),
            "timestamp": datetime.now().isoformat(),
            "chain_integrity": self.verify_chain_integrity()
        }
    
    def _sign_transaction(self, transaction: Transaction) -> str:
        """Sign a transaction using HMAC."""
        message = json.dumps(transaction.to_dict(), sort_keys=True)
        secret = self.config.get("blockchain_secret", "nuclear-intelligence-secret")
        return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    
    def get_knowledge_records(self) -> List[Dict[str, Any]]:
        """Get all knowledge records (NES minting transactions) from the blockchain."""
        records = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.tx_type == TransactionType.NES_MINT:
                    records.append({
                        "block": block.block_number,
                        "tx": tx.tx_id,
                        "data": tx.data,
                        "timestamp": tx.timestamp,
                        "block_hash": block.calculate_hash()
                    })
        return records
    
    def get_external_minting_queue(self) -> List[Dict[str, Any]]:
        """Get the queue of transactions pending external minting."""
        return self.external_minting_queue
    
    def process_external_minting(self, tx_id: str, external_tx_hash: str) -> bool:
        """Mark a transaction as successfully minted on external network."""
        for item in self.external_minting_queue:
            if item["tx_id"] == tx_id:
                item["status"] = "external_minted"
                item["external_tx_hash"] = external_tx_hash
                item["external_mint_time"] = datetime.now().isoformat()
                
                # Update transaction history
                for hist in self.transaction_history:
                    if hist["tx_id"] == tx_id:
                        hist["status"] = "fully_confirmed"
                        hist["external_tx_hash"] = external_tx_hash
                
                self.logger.info(f"Transaction {tx_id} successfully minted externally.")
                return True
        
        self.logger.warning(f"Transaction {tx_id} not found in external minting queue.")
        return False
    
    def export_ledger(self) -> Dict[str, Any]:
        """Export the complete ledger state."""
        return {
            "chain": [block.to_dict() for block in self.chain],
            "balances": self.balances,
            "transaction_history": self.transaction_history,
            "external_minting_queue": self.external_minting_queue,
            "chain_state": self.get_chain_state(),
            "export_timestamp": datetime.now().isoformat()
        }
    
    def get_nes_balance(self, address: str) -> float:
        """Get NES token balance for an address."""
        return self.balances.get(address, 0.0)
    
    def transfer_nes_token(self, sender: str, receiver: str, amount: float) -> Optional[str]:
        """Transfer NES tokens between addresses."""
        if self.balances.get(sender, 0.0) < amount:
            self.logger.error(f"Insufficient balance for {sender}")
            return None
        
        self.balances[sender] -= amount
        if receiver not in self.balances:
            self.balances[receiver] = 0.0
        self.balances[receiver] += amount
        
        tx_id = self.add_transaction(
            tx_type=TransactionType.NES_TRANSFER,
            data={"amount": amount},
            sender=sender,
            receiver=receiver,
            amount=amount
        )
        
        return tx_id


# ==================== Main Execution ====================

def main():
    """Main execution function."""
    config = {
        "llm_model_large": "gpt-4-turbo",
        "blockchain_secret": "nuclear-intelligence-secret"
    }
    
    ledger = EnhancedVirtualLedger(config)
    
    # Simulate minting a NES token
    mint_result = ledger.mint_nes_token(
        answer_id="ans_12345",
        question="What is the future of thorium-based nuclear reactors?",
        answer="Thorium-based reactors offer several advantages...",
        evaluation_scores={
            "scientific_accuracy": 95,
            "novelty_score": 88,
            "usefulness_score": 92,
            "self_consistency": 96,
            "overall_score": 93
        },
        answer_metadata={"model": "gpt-4-turbo", "source": "nuclear_intelligence"}
    )
    
    print("Mint Result:", json.dumps(mint_result, indent=2))
    
    # Mine a block
    mined_block = ledger.mine_pending_block()
    if mined_block:
        print(f"\nBlock {mined_block.block_number} mined successfully!")
        print(f"Block Hash: {mined_block.calculate_hash()}")
    
    # Get chain state
    state = ledger.get_chain_state()
    print("\nChain State:", json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
