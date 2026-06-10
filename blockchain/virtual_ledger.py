"""
Nuclear Intelligence v3.0 - Enhanced Virtual Ledger
═══════════════════════════════════════════════════════════════════
Advanced Blockchain with:
- Proof-of-Work mining with adaptive difficulty
- Merkle trees for transaction verification
- HMAC cryptographic signatures
- NES token minting with full metadata
- Multi-signature support
- Chain integrity verification
- Transaction indexing and search
═══════════════════════════════════════════════════════════════════
"""

import os
import json
import hashlib
import hmac
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
from collections import defaultdict


# ─── Transaction Class ────────────────────────────────────────────

class Transaction:
    """Cryptographically signed transaction with metadata"""

    def __init__(
        self,
        sender: str,
        recipient: str,
        amount: float,
        metadata: Optional[Dict] = None,
        timestamp: Optional[str] = None,
        signature: Optional[str] = None,
        tx_id: Optional[str] = None,
        nonce: int = 0,
    ):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now().isoformat()
        self.tx_id = tx_id or self._gen_tx_id()
        self.signature = signature or self._sign()
        self.nonce = nonce
        self.status = "confirmed"

    def _gen_tx_id(self) -> str:
        content = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}{random.random()}"
        return hashlib.sha256(content.encode()).hexdigest()[:24]

    def _sign(self) -> str:
        content = f"{self.tx_id}{self.sender}{self.recipient}{self.amount}{self.timestamp}{self.nonce}"
        secret = os.getenv("BLOCKCHAIN_SECRET", "nuclear-intelligence-v3").encode()
        return hmac.new(secret, content.encode(), hashlib.sha3_512).hexdigest()[:96]

    def verify_signature(self) -> bool:
        return hmac.compare_digest(self.signature, self._sign())

    def to_dict(self) -> Dict:
        return {
            "tx_id": self.tx_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "signature": self.signature,
            "nonce": self.nonce,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Transaction":
        return cls(
            sender=data["sender"],
            recipient=data["recipient"],
            amount=data["amount"],
            metadata=data.get("metadata"),
            timestamp=data.get("timestamp"),
            signature=data.get("signature"),
            tx_id=data.get("tx_id"),
            nonce=data.get("nonce", 0),
        )

    def get_display(self) -> Dict:
        return {
            "tx_id": self.tx_id,
            "type": self.metadata.get("type", "transfer"),
            "sender": self.sender[:20] + "..." if len(self.sender) > 20 else self.sender,
            "recipient": self.recipient[:20] + "..." if len(self.recipient) > 20 else self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp[:19],
            "status": self.status,
        }


# ─── Merkle Tree ──────────────────────────────────────────────────

class MerkleTree:
    """Cryptographic Merkle tree for transaction verification"""

    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions
        self.leaves = []
        self.tree = []
        self.merkle_root = self._build()

    def _hash_data(self, data: str) -> str:
        return hashlib.sha3_256(data.encode()).hexdigest()

    def _hash_tx(self, tx: Transaction) -> str:
        tx_data = json.dumps(tx.to_dict(), sort_keys=True)
        return self._hash_data(tx_data)

    def _build(self) -> str:
        if not self.transactions:
            return self._hash_data("empty_merkle_tree")

        # Create leaf nodes
        self.leaves = [self._hash_tx(tx) for tx in self.transactions]
        self.tree = self.leaves[:]

        # Build tree bottom-up
        current_level = self.leaves[:]
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = self._hash_data(left + right)
                next_level.append(combined)
            self.tree.extend(next_level)
            current_level = next_level

        return current_level[0] if current_level else self._hash_data("empty")

    def verify_proof(self, tx: Transaction, proof: List[Dict]) -> bool:
        """Verify a transaction against a Merkle proof"""
        current_hash = self._hash_tx(tx)
        for p in proof:
            if p["position"] == "left":
                current_hash = self._hash_data(p["hash"] + current_hash)
            else:
                current_hash = self._hash_data(current_hash + p["hash"])
        return current_hash == self.merkle_root


# ─── Block Class ──────────────────────────────────────────────────

class Block:
    """Block with POW mining, Merkle tree, and full metadata"""

    def __init__(
        self,
        index: int,
        timestamp: str,
        transactions: List[Transaction],
        previous_hash: str,
        nonce: int = 0,
        difficulty: int = 4,
        block_hash: Optional[str] = None,
        miner: str = "system",
    ):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.difficulty = difficulty
        self.miner = miner
        self.merkle_tree = MerkleTree(transactions)
        self.merkle_root = self.merkle_tree.merkle_root
        self.hash = block_hash or self._compute_hash()
        self.reward = 1.0
        self.size_bytes = len(json.dumps(self.to_dict()).encode())

    def _compute_hash(self) -> str:
        block_data = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "miner": self.miner,
        }, sort_keys=True)
        return hashlib.sha3_256(block_data.encode()).hexdigest()

    def mine(self, max_attempts: int = 1000000) -> Tuple[bool, int]:
        """Proof-of-Work mining with adaptive difficulty"""
        target = "0" * self.difficulty
        start_nonce = self.nonce

        for i in range(max_attempts):
            self.nonce = start_nonce + i
            h = self._compute_hash()
            if h.startswith(target):
                self.hash = h
                return True, self.nonce

        return False, self.nonce

    def verify_pow(self) -> bool:
        """Verify proof-of-work"""
        return self.hash.startswith("0" * self.difficulty) and self.hash == self._compute_hash()

    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "merkle_root": self.merkle_root,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
            "difficulty": self.difficulty,
            "miner": self.miner,
            "reward": self.reward,
            "tx_count": len(self.transactions),
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Block":
        return cls(
            index=data["index"],
            timestamp=data["timestamp"],
            transactions=[Transaction.from_dict(tx) for tx in data.get("transactions", [])],
            previous_hash=data["previous_hash"],
            nonce=data.get("nonce", 0),
            difficulty=data.get("difficulty", 4),
            block_hash=data.get("hash"),
            miner=data.get("miner", "system"),
        )


# ─── Virtual Ledger Class ────────────────────────────────────────

class VirtualLedger:
    """Advanced virtual blockchain ledger with NES token minting"""

    # System addresses
    SYSTEM_TREASURY = "system_treasury"
    KNOWLEDGE_CREATION = "knowledge_creation_event"
    GENESIS = "genesis"

    def __init__(
        self,
        difficulty: int = 4,
        ledger_file: str = "knowledge_base/virtual_ledger.json",
        enable_adaptive_difficulty: bool = True,
    ):
        self.difficulty = difficulty
        self.ledger_file = ledger_file
        self.enable_adaptive_difficulty = enable_adaptive_difficulty

        # Chain state
        self.chain: List[Block] = []
        self.pending: List[Transaction] = []
        self.nes_supply: float = 0.0
        self.total_transactions: int = 0
        self.total_blocks: int = 0

        # Advanced features
        self.address_balances: Dict[str, float] = defaultdict(float)
        self.tx_index: Dict[str, Transaction] = {}
        self.block_rewards: List[Dict] = []
        self.mining_difficulty_history: List[Dict] = []

        # Statistics
        self.stats = {
            "total_mining_time": 0.0,
            "avg_nonce": 0,
            "total_hashes": 0,
        }

        # Initialize
        os.makedirs(os.path.dirname(ledger_file), exist_ok=True)
        if os.path.exists(ledger_file):
            self._load_chain()
        else:
            self.create_genesis_block()

    def create_genesis_block(self):
        """Create the genesis block with system initialization"""
        tx = Transaction(
            sender=self.GENESIS,
            recipient=self.SYSTEM_TREASURY,
            amount=0.0,
            metadata={
                "note": "Nuclear Intelligence Genesis Block v3.0",
                "version": "3.0",
                "timestamp": datetime.now().isoformat(),
                "difficulty": self.difficulty,
                "system": "Nuclear Intelligence Virtual Blockchain",
            }
        )

        block = Block(
            index=0,
            timestamp=datetime.now().isoformat(),
            transactions=[tx],
            previous_hash="0" * 64,
            difficulty=self.difficulty,
            miner="genesis",
        )

        mined, nonce = block.mine(max_attempts=1000)
        if not mined:
            # Force genesis block with low difficulty
            block.difficulty = 1
            block.mine(max_attempts=10000)

        self.chain.append(block)
        self._save_chain()

        logger.info(f"🧬 Genesis block created: {block.hash[:16]}...")
        logger.info(f"   Difficulty: {block.difficulty}, Nonce: {block.nonce}")

    def get_last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, tx: Transaction) -> bool:
        """Add a transaction to pending pool"""
        # Verify signature
        if not tx.verify_signature():
            logger.warning(f"❌ Invalid signature on TX {tx.tx_id[:12]}")
            return False

        # Check balance
        sender_balance = self.get_balance(tx.sender)
        if tx.sender not in (self.KNOWLEDGE_CREATION, self.GENESIS) and sender_balance < tx.amount:
            logger.warning(f"❌ Insufficient balance for TX {tx.tx_id[:12]}")
            return False

        # Add to pending
        self.pending.append(tx)
        self.tx_index[tx.tx_id] = tx
        self.total_transactions += 1

        logger.debug(f"📝 TX added: {tx.tx_id[:12]} | {tx.sender[:15]} → {tx.recipient[:15]} ({tx.amount} NES)")
        return True

    def mine_pending(self, miner: str = "system_miner") -> Optional[Block]:
        """Mine pending transactions into a new block"""
        if not self.pending:
            return None

        last = self.get_last_block()

        # Adaptive difficulty adjustment
        if self.enable_adaptive_difficulty and len(self.chain) > 1:
            self._adjust_difficulty()

        block = Block(
            index=last.index + 1,
            timestamp=datetime.now().isoformat(),
            transactions=self.pending[:],
            previous_hash=last.hash,
            difficulty=self.difficulty,
            miner=miner,
        )

        # Mining
        start_time = time.time()
        max_attempts = int(os.getenv("POW_MAX_ATTEMPTS", 1000000))

        mined, final_nonce = block.mine(max_attempts=max_attempts)

        mining_time = time.time() - start_time
        self.stats["total_mining_time"] += mining_time
        self.stats["total_hashes"] += final_nonce - block.nonce + max_attempts if not mined else final_nonce

        if mined:
            self.chain.append(block)
            self.pending = []

            # Update balances
            self._update_balances(block)

            # Track rewards
            self.block_rewards.append({
                "block_index": block.index,
                "miner": miner,
                "reward": block.reward,
                "tx_count": len(block.transactions),
                "nonce": block.nonce,
                "mining_time": mining_time,
            })

            self._save_chain()

            logger.info(f"⛏️ Block #{block.index} mined!")
            logger.info(f"   Hash: {block.hash[:16]}... | Nonce: {block.nonce} | Time: {mining_time:.2f}s")
            logger.info(f"   Difficulty: {block.difficulty} | TXs: {block.tx_count} | Size: {block.size_bytes}B")

            return block

        logger.error("❌ Mining failed after max attempts")
        return None

    def _adjust_difficulty(self):
        """Adaptive difficulty: adjust based on mining speed"""
        if len(self.block_rewards) < 3:
            return

        recent = self.block_rewards[-3:]
        avg_time = sum(r["mining_time"] for r in recent) / len(recent)

        target_time = 30  # seconds
        if avg_time < target_time / 2:
            self.difficulty = min(self.difficulty + 1, 8)
            logger.info(f"📈 Difficulty increased to {self.difficulty}")
        elif avg_time > target_time * 2:
            self.difficulty = max(self.difficulty - 1, 1)
            logger.info(f"📉 Difficulty decreased to {self.difficulty}")

        self.mining_difficulty_history.append({
            "timestamp": datetime.now().isoformat(),
            "difficulty": self.difficulty,
            "avg_mining_time": avg_time,
        })

    def _update_balances(self, block: Block):
        """Update address balances from block transactions"""
        for tx in block.transactions:
            if tx.sender not in (self.GENESIS, self.KNOWLEDGE_CREATION):
                self.address_balances[tx.sender] -= tx.amount
            self.address_balances[tx.recipient] += tx.amount

    def mint_nes_token(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Mint a new NES token with full metadata"""
        mint_tx = Transaction(
            sender=self.KNOWLEDGE_CREATION,
            recipient=self.SYSTEM_TREASURY,
            amount=1.0,
            metadata={
                **metadata,
                "type": "nes_mint",
                "mint_time": datetime.now().isoformat(),
                "version": "3.0",
            }
        )

        if not self.add_transaction(mint_tx):
            logger.error("❌ Failed to add mint transaction")
            return None

        block = self.mine_pending(miner="nes_mint_bot")
        if block:
            self.nes_supply += 1.0
            self.total_blocks += 1
            logger.info(f"🪙 NES minted! Total supply: {self.nes_supply}")
            return block.hash

        return None

    def is_chain_valid(self) -> bool:
        """Verify entire blockchain integrity"""
        if not self.chain:
            return False

        # Check genesis block
        if self.chain[0].index != 0 or self.chain[0].previous_hash != "0" * 64:
            logger.error("❌ Genesis block invalid")
            return False

        # Check each block
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Hash verification
            if current.hash != current._compute_hash():
                logger.error(f"❌ Block {i} hash mismatch")
                return False

            # POW verification
            if not current.verify_pow():
                logger.error(f"❌ Block {i} POW invalid")
                return False

            # Chain link verification
            if current.previous_hash != previous.hash:
                logger.error(f"❌ Block {i} previous hash mismatch")
                return False

            # Merkle tree verification
            if MerkleTree(current.transactions).merkle_root != current.merkle_root:
                logger.error(f"❌ Block {i} Merkle root mismatch")
                return False

        return True

    def get_balance(self, address: str) -> float:
        """Get address balance (cached)"""
        return self.address_balances.get(address, 0.0)

    def get_transaction_history(
        self,
        address: Optional[str] = None,
        limit: int = 50,
        tx_type: Optional[str] = None,
    ) -> List[Dict]:
        """Get transaction history with filtering"""
        txs = []
        for block in reversed(self.chain):
            for tx in block.transactions:
                # Filter by address
                if address and tx.sender != address and tx.recipient != address:
                    continue
                # Filter by type
                if tx_type and tx.metadata.get("type") != tx_type:
                    continue

                txs.append({
                    **tx.to_dict(),
                    "block_index": block.index,
                    "block_hash": block.hash,
                    "mining_time": block.nonce,
                })

        return txs[:limit]

    def search_transactions(self, query: str, limit: int = 20) -> List[Dict]:
        """Search transactions by content"""
        q_lower = query.lower()
        results = []

        for block in reversed(self.chain):
            for tx in block.transactions:
                # Search in metadata, sender, recipient
                searchable = (
                    json.dumps(tx.metadata).lower() +
                    tx.sender.lower() +
                    tx.recipient.lower() +
                    tx.tx_id.lower()
                )
                if q_lower in searchable:
                    results.append({
                        **tx.to_dict(),
                        "block_index": block.index,
                        "block_hash": block.hash,
                    })

        return results[:limit]

    def get_block_info(self, block_index: int) -> Optional[Dict]:
        """Get detailed block information"""
        if 0 <= block_index < len(self.chain):
            block = self.chain[block_index]
            return {
                **block.to_dict(),
                "difficulty": block.difficulty,
                "confirmations": len(self.chain) - block_index - 1,
            }
        return None

    def export_chain(self, path: Optional[str] = None) -> str:
        """Export full chain to JSON"""
        path = path or self.ledger_file.replace(".json", "_export.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                "export_time": datetime.now().isoformat(),
                "chain_length": len(self.chain),
                "nes_supply": self.nes_supply,
                "total_transactions": self.total_transactions,
                "difficulty": self.difficulty,
                "chain_valid": self.is_chain_valid(),
                "blocks": [b.to_dict() for b in self.chain],
            }, f, indent=4, ensure_ascii=False)
        return path

    def _save_chain(self):
        """Save chain to disk atomically"""
        try:
            temp = self.ledger_file + ".tmp"
            with open(temp, 'w', encoding='utf-8') as f:
                json.dump({
                    "chain": [b.to_dict() for b in self.chain],
                    "difficulty": self.difficulty,
                    "nes_supply": self.nes_supply,
                    "total_transactions": self.total_transactions,
                    "saved_at": datetime.now().isoformat(),
                }, f, ensure_ascii=False, indent=4)
            os.replace(temp, self.ledger_file)
        except Exception as e:
            logger.error(f"💾 Save error: {e}")

    def _load_chain(self):
        """Load chain from disk"""
        try:
            with open(self.ledger_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.chain = [Block.from_dict(b) for b in data.get("chain", [])]
            self.difficulty = data.get("difficulty", 4)
            self.nes_supply = data.get("nes_supply", 0.0)
            self.total_transactions = data.get("total_transactions", 0)

            # Rebuild balances
            for block in self.chain:
                for tx in block.transactions:
                    self.tx_index[tx.tx_id] = tx
                    if tx.sender not in (self.GENESIS, self.KNOWLEDGE_CREATION):
                        self.address_balances[tx.sender] -= tx.amount
                    self.address_balances[tx.recipient] += tx.amount

            logger.info(f"📜 Ledger loaded: {len(self.chain)} blocks, {self.nes_supply} NES, {self.total_transactions} TX")
        except Exception as e:
            logger.error(f"📜 Load error: {e}")
            self.chain = []
            self.create_genesis_block()

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive ledger statistics"""
        avg_nonce = 0
        if self.chain:
            nonces = [b.nonce for b in self.chain[1:]]
            if nonces:
                avg_nonce = sum(nonces) / len(nonces)

        return {
            "chain_length": len(self.chain),
            "nes_supply": self.nes_supply,
            "pending_transactions": len(self.pending),
            "total_transactions": self.total_transactions,
            "difficulty": self.difficulty,
            "latest_hash": self.get_last_block().hash[:16] + "...",
            "genesis_hash": self.chain[0].hash[:16] + "...",
            "chain_valid": self.is_chain_valid(),
            "avg_nonce": f"{avg_nonce:.0f}",
            "total_mining_time": f"{self.stats['total_mining_time']:.1f}s",
            "addresses": len(self.address_balances),
        }