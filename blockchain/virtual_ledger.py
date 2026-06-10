
import hashlib
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

class Transaction:
    def __init__(self, sender: str, recipient: str, amount: float, metadata: Dict[str, Any] = None, timestamp: str = None, signature: str = None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = timestamp or datetime.now().isoformat()
        self.metadata = metadata if metadata is not None else {}
        self.signature = signature or self._generate_signature()

    def _generate_signature(self) -> str:
        # Simplified signature for virtual ledger
        tx_content = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}{json.dumps(self.metadata, sort_keys=True)}"
        return hashlib.sha256(tx_content.encode()).hexdigest()

    def to_dict(self):
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "signature": self.signature
        }

class Block:
    def __init__(self, index: int, timestamp: str, transactions: List[Transaction], previous_hash: str, nonce: int = 0, hash: str = None):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = hash or self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }

class VirtualLedger:
    def __init__(self, difficulty=3, ledger_file="knowledge_base/virtual_ledger.json"):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.difficulty = difficulty
        self.ledger_file = ledger_file
        self.nes_supply = 0.0
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.ledger_file), exist_ok=True)

        # Load existing chain or create genesis block
        if os.path.exists(self.ledger_file):
            self._load_chain()
        else:
            self.create_genesis_block()

    def create_genesis_block(self):
        genesis_tx = Transaction("system", "genesis", 0.0, {"note": "Nuclear Intelligence Genesis Block"})
        genesis_block = Block(0, datetime.now().isoformat(), [genesis_tx], "0")
        genesis_block.hash = self.proof_of_work(genesis_block)
        self.chain.append(genesis_block)
        self._save_chain()
        logger.info("Genesis block created.")

    def get_last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, transaction: Transaction):
        self.pending_transactions.append(transaction)
        logger.info(f"Transaction added: {transaction.sender} -> {transaction.recipient} ({transaction.amount} NES)")

    def proof_of_work(self, block: Block):
        block.nonce = 0
        computed_hash = block.calculate_hash()
        while not computed_hash.startswith("0" * self.difficulty):
            block.nonce += 1
            computed_hash = block.calculate_hash()
        return computed_hash

    def mine_pending_transactions(self, miner_address: str = "system_miner") -> Optional[Block]:
        if not self.pending_transactions:
            return None

        last_block = self.get_last_block()
        new_block = Block(
            index=last_block.index + 1,
            timestamp=datetime.now().isoformat(),
            transactions=self.pending_transactions,
            previous_hash=last_block.hash
        )
        new_block.hash = self.proof_of_work(new_block)

        self.chain.append(new_block)
        self.pending_transactions = [] 
        self._save_chain()
        logger.info(f"Block #{new_block.index} mined successfully. Hash: {new_block.hash}")
        return new_block

    def mint_nes_token(self, metadata: Dict[str, Any]):
        # Each validated scientific advancement mints exactly 1 NES token
        mint_transaction = Transaction(
            sender="knowledge_creation_event",
            recipient="system_treasury",
            amount=1.0,
            metadata=metadata
        )
        self.add_transaction(mint_transaction)
        self.nes_supply += 1.0
        logger.info(f"1 NES token minted for scientific advancement. Total supply: {self.nes_supply}")
        self.mine_pending_transactions()

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            if current_block.hash != current_block.calculate_hash():
                logger.error(f"Block {current_block.index} hash mismatch.")
                return False

            if current_block.previous_hash != previous_block.hash:
                logger.error(f"Block {current_block.index} previous hash mismatch.")
                return False

            if not current_block.hash.startswith("0" * self.difficulty):
                logger.error(f"Block {current_block.index} POW invalid.")
                return False
        return True

    def _save_chain(self):
        with open(self.ledger_file, 'w', encoding='utf-8') as f:
            json.dump([block.to_dict() for block in self.chain], f, ensure_ascii=False, indent=4)

    def _load_chain(self):
        try:
            with open(self.ledger_file, 'r', encoding='utf-8') as f:
                chain_data = json.load(f)
                self.chain = []
                for block_data in chain_data:
                    transactions = [
                        Transaction(
                            tx['sender'], 
                            tx['recipient'], 
                            tx['amount'], 
                            tx.get('metadata'),
                            tx.get('timestamp'),
                            tx.get('signature')
                        ) 
                        for tx in block_data['transactions']
                    ]
                    block = Block(
                        block_data['index'], 
                        block_data['timestamp'], 
                        transactions, 
                        block_data['previous_hash'], 
                        block_data['nonce'], 
                        block_data['hash']
                    )
                    self.chain.append(block)
                
                # Calculate NES supply
                self.nes_supply = sum(
                    tx.amount for block in self.chain for tx in block.transactions 
                    if tx.recipient == "system_treasury" and tx.sender == "knowledge_creation_event"
                )
            logger.info(f"Ledger loaded. Supply: {self.nes_supply} NES, Blocks: {len(self.chain)}")
        except Exception as e:
            logger.error(f"Failed to load ledger: {e}")
            self.create_genesis_block()

    def get_balance(self, address: str) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.recipient == address:
                    balance += tx.amount
                if tx.sender == address:
                    balance -= tx.amount
        return balance
