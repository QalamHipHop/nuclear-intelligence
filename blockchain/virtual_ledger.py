"""Nuclear Intelligence - Enhanced Virtual Ledger v2.0
Blockchain with Merkle trees, POW, HMAC signatures, NES minting"""
import os, json, hashlib, hmac, time
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

class Transaction:
    def __init__(self, sender: str, recipient: str, amount: float, metadata: Optional[Dict] = None,
                 timestamp: Optional[str] = None, signature: Optional[str] = None, tx_id: Optional[str] = None):
        self.sender = sender; self.recipient = recipient; self.amount = amount
        self.timestamp = timestamp or datetime.now().isoformat()
        self.metadata = metadata or {}; self.tx_id = tx_id or self._gen_tx_id()
        self.signature = signature or self._sign()

    def _gen_tx_id(self) -> str:
        return hashlib.sha256(f"{self.sender}{self.recipient}{self.amount}{self.timestamp}".encode()).hexdigest()[:24]

    def _sign(self) -> str:
        content = f"{self.tx_id}{self.sender}{self.recipient}{self.amount}{self.timestamp}"
        secret = os.getenv("BLOCKCHAIN_SECRET", "nuclear-intelligence").encode()
        return hmac.new(secret, content.encode(), hashlib.sha256).hexdigest()[:64]

    def verify_signature(self) -> bool:
        return hmac.compare_digest(self.signature, self._sign())

    def to_dict(self) -> Dict:
        return {"tx_id": self.tx_id, "sender": self.sender, "recipient": self.recipient,
                "amount": self.amount, "timestamp": self.timestamp, "metadata": self.metadata, "signature": self.signature}

    @classmethod
    def from_dict(cls, data: Dict) -> "Transaction":
        return cls(data["sender"], data["recipient"], data["amount"], data.get("metadata"),
                   data.get("timestamp"), data.get("signature"), data.get("tx_id"))

class MerkleTree:
    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions
        self.merkle_root = self._build()

    def _hash_tx(self, tx: Transaction) -> str:
        return hashlib.sha256(json.dumps(tx.to_dict(), sort_keys=True).encode()).hexdigest()

    def _build(self) -> str:
        if not self.transactions:
            return hashlib.sha256(b"empty").hexdigest()
        hashes = [self._hash_tx(tx) for tx in self.transactions]
        while len(hashes) > 1:
            if len(hashes) % 2: hashes.append(hashes[-1])
            hashes = [hashlib.sha256((hashes[i] + hashes[i+1]).encode()).hexdigest() for i in range(0, len(hashes), 2)]
        return hashes[0]

class Block:
    def __init__(self, index: int, timestamp: str, transactions: List[Transaction],
                 previous_hash: str, nonce: int = 0, difficulty: int = 4, block_hash: Optional[str] = None):
        self.index = index; self.timestamp = timestamp; self.transactions = transactions
        self.previous_hash = previous_hash; self.nonce = nonce; self.difficulty = difficulty
        self.merkle_tree = MerkleTree(transactions)
        self.merkle_root = self.merkle_tree.merkle_root
        self.hash = block_hash or self._compute_hash()

    def _compute_hash(self) -> str:
        return hashlib.sha256(json.dumps({"index": self.index, "timestamp": self.timestamp,
            "merkle_root": self.merkle_root, "previous_hash": self.previous_hash, "nonce": self.nonce}, sort_keys=True).encode()).hexdigest()

    def mine(self, max_attempts: int = 1000000) -> bool:
        target = "0" * self.difficulty
        for i in range(max_attempts):
            self.nonce = i
            h = self._compute_hash()
            if h.startswith(target):
                self.hash = h
                return True
        return False

    def to_dict(self) -> Dict:
        return {"index": self.index, "timestamp": self.timestamp,
                "transactions": [tx.to_dict() for tx in self.transactions],
                "merkle_root": self.merkle_root, "previous_hash": self.previous_hash,
                "nonce": self.nonce, "hash": self.hash, "difficulty": self.difficulty, "tx_count": len(self.transactions)}

    @classmethod
    def from_dict(cls, data: Dict) -> "Block":
        return cls(data["index"], data["timestamp"],
                   [Transaction.from_dict(tx) for tx in data.get("transactions", [])],
                   data["previous_hash"], data.get("nonce", 0), data.get("difficulty", 4), data.get("hash"))

class VirtualLedger:
    def __init__(self, difficulty: int = 4, ledger_file: str = "knowledge_base/virtual_ledger.json"):
        self.difficulty = difficulty; self.ledger_file = ledger_file
        self.chain: List[Block] = []; self.pending: List[Transaction] = []
        self.nes_supply = 0.0; self.total_transactions = 0
        os.makedirs(os.path.dirname(ledger_file), exist_ok=True)
        if os.path.exists(ledger_file): self._load_chain()
        else: self.create_genesis_block()

    def create_genesis_block(self):
        tx = Transaction("system", "genesis", 0.0, {"note": "Nuclear Intelligence Genesis", "version": "2.0"})
        block = Block(0, datetime.now().isoformat(), [tx], "0" * 64, difficulty=self.difficulty)
        block.mine()
        self.chain.append(block); self._save_chain()
        logger.info(f"Genesis block: {block.hash[:16]}...")

    def get_last_block(self) -> Block: return self.chain[-1]

    def add_transaction(self, tx: Transaction) -> bool:
        if not tx.verify_signature(): logger.warning(f"Invalid signature on {tx.tx_id}"); return False
        self.pending.append(tx); self.total_transactions += 1
        logger.info(f"Transaction: {tx.tx_id[:12]} | {tx.sender} → {tx.recipient} ({tx.amount} NES)")
        return True

    def mine_pending(self, miner: str = "system_miner") -> Optional[Block]:
        if not self.pending: return None
        last = self.get_last_block()
        block = Block(last.index + 1, datetime.now().isoformat(), self.pending, last.hash, difficulty=self.difficulty)
        if block.mine():
            self.chain.append(block); self.pending = []; self._save_chain()
            logger.info(f"Block #{block.index} mined. Hash: {block.hash[:16]}... Nonce: {block.nonce}")
            return block
        return None

    def mint_nes_token(self, metadata: Dict[str, Any]) -> Optional[str]:
        tx = Transaction("knowledge_creation_event", "system_treasury", 1.0, {**metadata, "type": "nes_mint", "mint_time": datetime.now().isoformat()})
        self.add_transaction(tx)
        block = self.mine_pending()
        if block:
            self.nes_supply += 1.0
            logger.info(f"NES minted! Total: {self.nes_supply}")
            return block.hash
        return None

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            c, p = self.chain[i], self.chain[i-1]
            if c.hash != c._compute_hash(): logger.error(f"Block {i} hash mismatch"); return False
            if c.previous_hash != p.hash: logger.error(f"Block {i} prev hash mismatch"); return False
            if not c.hash.startswith("0" * c.difficulty): logger.error(f"Block {i} POW invalid"); return False
            if MerkleTree(c.transactions).merkle_root != c.merkle_root: logger.error(f"Block {i} Merkle mismatch"); return False
        return True

    def get_balance(self, addr: str) -> float:
        bal = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.recipient == addr: bal += tx.amount
                if tx.sender == addr: bal -= tx.amount
        return bal

    def get_transaction_history(self, addr: Optional[str] = None, limit: int = 50) -> List[Dict]:
        txs = []
        for block in reversed(self.chain):
            for tx in block.transactions:
                if addr is None or tx.sender == addr or tx.recipient == addr:
                    txs.append({**tx.to_dict(), "block_index": block.index, "block_hash": block.hash})
        return txs[:limit]

    def _save_chain(self):
        try:
            temp = self.ledger_file + ".tmp"
            with open(temp, 'w', encoding='utf-8') as f: json.dump([b.to_dict() for b in self.chain], f, ensure_ascii=False, indent=4)
            os.replace(temp, self.ledger_file)
        except Exception as e: logger.error(f"Save error: {e}")

    def _load_chain(self):
        try:
            with open(self.ledger_file, 'r', encoding='utf-8') as f:
                self.chain = [Block.from_dict(b) for b in json.load(f)]
            self.nes_supply = sum(tx.amount for block in self.chain for tx in block.transactions if tx.sender == "knowledge_creation_event" and tx.recipient == "system_treasury")
            self.total_transactions = sum(len(b.transactions) for b in self.chain)
            logger.info(f"Ledger loaded: {len(self.chain)} blocks, {self.nes_supply} NES, {self.total_transactions} TX")
        except Exception as e:
            logger.error(f"Load error: {e}"); self.chain = []; self.create_genesis_block()

    def export_chain(self, path: Optional[str] = None) -> str:
        path = path or self.ledger_file.replace(".json", "_export.json")
        with open(path, 'w', encoding='utf-8') as f: json.dump({"export_time": datetime.now().isoformat(), "chain_length": len(self.chain), "nes_supply": self.nes_supply, "total_transactions": self.total_transactions, "blocks": [b.to_dict() for b in self.chain]}, f, indent=4, ensure_ascii=False)
        return path

    def get_stats(self) -> Dict[str, Any]:
        return {"chain_length": len(self.chain), "nes_supply": self.nes_supply, "pending_transactions": len(self.pending), "total_transactions": self.total_transactions, "difficulty": self.difficulty, "latest_hash": self.get_last_block().hash[:16]+"...", "genesis_hash": self.chain[0].hash[:16]+"...", "chain_valid": self.is_chain_valid()}
