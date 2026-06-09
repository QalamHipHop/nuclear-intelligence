
import hashlib
import json
import time
import hmac
from datetime import datetime
from typing import List, Dict, Any, Optional

class Transaction:
    def __init__(self, sender: str, recipient: str, amount: float, metadata: Dict[str, Any] = None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = datetime.now().isoformat()
        self.metadata = metadata if metadata is not None else {}

    def to_dict(self):
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }

    def __str__(self):
        return json.dumps(self.to_dict(), indent=2)

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

    def __str__(self):
        return json.dumps(self.to_dict(), indent=2)

class VirtualLedger:
    def __init__(self, difficulty=2, ledger_file="blockchain/virtual_ledger.json"):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.difficulty = difficulty
        self.ledger_file = ledger_file
        self.nes_supply = 0.0

        # Load existing chain or create genesis block
        if os.path.exists(self.ledger_file):
            self._load_chain()
        else:
            self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, datetime.now().isoformat(), [], "0")
        self.chain.append(genesis_block)
        self._save_chain()

    def get_last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, transaction: Transaction):
        self.pending_transactions.append(transaction)

    def proof_of_work(self, block: Block):
        block.nonce = 0
        computed_hash = block.calculate_hash()
        while not computed_hash.startswith("0" * self.difficulty):
            block.nonce += 1
            computed_hash = block.calculate_hash()
        return computed_hash

    def mine_pending_transactions(self, miner_address: str = "system_miner") -> Optional[Block]:
        if not self.pending_transactions:
            print("No pending transactions to mine.")
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
        self.pending_transactions = [] # Clear pending transactions after mining
        self._save_chain()
        print(f"Block #{new_block.index} mined with hash: {new_block.hash}")
        return new_block

    def mint_nes_token(self, metadata: Dict[str, Any]):
        # NES token minting is tied to validated scientific advancement
        # For each validated advancement, 1 NES token is minted.
        # The 'recipient' of this minting transaction is the 'system_treasury' or similar.
        # The 'sender' can be considered 'knowledge_creation_event'.
        mint_transaction = Transaction(
            sender="knowledge_creation_event",
            recipient="system_treasury", # Or a specific address for the project
            amount=1.0, # Exactly 1 NES token
            metadata=metadata
        )
        self.add_transaction(mint_transaction)
        self.nes_supply += 1.0
        print(f"1 NES token minted. Total supply: {self.nes_supply}")
        # Immediately mine the block containing the minting transaction
        self.mine_pending_transactions()

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            if current_block.hash != current_block.calculate_hash():
                print(f"Block {current_block.index} hash mismatch.")
                return False

            if current_block.previous_hash != previous_block.hash:
                print(f"Block {current_block.index} previous hash mismatch.")
                return False

            if not current_block.hash.startswith("0" * self.difficulty):
                print(f"Block {current_block.index} does not meet difficulty requirement.")
                return False
        return True

    def _save_chain(self):
        with open(self.ledger_file, 'w', encoding='utf-8') as f:
            json.dump([block.to_dict() for block in self.chain], f, ensure_ascii=False, indent=4)

    def _load_chain(self):
        if os.path.exists(self.ledger_file):
            with open(self.ledger_file, 'r', encoding='utf-8') as f:
                chain_data = json.load(f)
                self.chain = []
                for block_data in chain_data:
                    transactions = [Transaction(tx['sender'], tx['recipient'], tx['amount'], tx['metadata']) for tx in block_data['transactions']]
                    block = Block(block_data['index'], block_data['timestamp'], transactions, block_data['previous_hash'], block_data['nonce'], block_data['hash'])
                    self.chain.append(block)
                # Recalculate NES supply from loaded chain
                self.nes_supply = sum(tx.amount for block in self.chain for tx in block.transactions if tx.recipient == "system_treasury" and tx.sender == "knowledge_creation_event")
            print(f"Virtual Ledger loaded from {self.ledger_file}. Current NES supply: {self.nes_supply}")

    def export_state(self, path: str):
        state = {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
            "nes_supply": self.nes_supply
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=4)
        print(f"Virtual Ledger state exported to {path}")


if __name__ == "__main__":
    # Example Usage
    ledger = VirtualLedger()
    print(f"Chain valid: {ledger.is_chain_valid()}")

    # Simulate a knowledge minting event
    knowledge_metadata = {
        "title": "Discovery of new nuclear fusion catalyst",
        "author": "AI Agent",
        "date": datetime.now().isoformat()
    }
    ledger.mint_nes_token(knowledge_metadata)

    # Add another transaction (e.g., transfer)
    tx2 = Transaction("user_A", "user_B", 0.5, {"purpose": "trade"})
    ledger.add_transaction(tx2)
    ledger.mine_pending_transactions("user_A")

    print(f"Chain valid: {ledger.is_chain_valid()}")
    ledger.export_state("virtual_ledger_export.json")

    # Simulate loading from file
    new_ledger = VirtualLedger()
    print(f"New ledger chain valid: {new_ledger.is_chain_valid()}")
    print(f"New ledger NES supply: {new_ledger.nes_supply}")

