import gradio as gr
import asyncio
import json
import hashlib
import hmac
import time
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path

# Third-party imports
from openai import AsyncOpenAI
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer, CrossEncoder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== Data Models ====================

class ResearchCategory(str, Enum):
    PHYSICS = "physics"
    ENGINEERING = "engineering"
    ECONOMICS = "economics"
    SAFETY = "safety"
    NOVEL_APPLICATIONS = "novel_applications"
    AI_INTEGRATION = "ai_integration"

@dataclass
class EvaluationScore:
    scientific_accuracy: float
    novelty_score: float
    usefulness_score: float
    self_consistency: float
    overall_score: float

    def dict(self):
        return asdict(self)

@dataclass
class ResearchQuestion:
    id: str
    question: str
    category: ResearchCategory
    complexity_level: int
    timestamp: datetime
    keywords: List[str] = field(default_factory=list)

@dataclass
class ResearchAnswer:
    id: str
    question_id: str
    answer: str
    sources: List[Dict[str, str]]
    equations: List[str]
    examples: List[str]
    citations: List[str]
    timestamp: datetime
    model_version: str
    evaluation_scores: EvaluationScore

# ==================== Blockchain ====================

class TransactionType(str, Enum):
    KNOWLEDGE_RECORD = "knowledge_record"
    NES_MINT = "nes_mint"
    NES_TRANSFER = "nes_transfer"

@dataclass
class Transaction:
    tx_id: str
    tx_type: TransactionType
    timestamp: float
    data: Dict[str, Any]
    sender: str
    receiver: str
    amount: float
    nonce: int
    signature: str = ""

    def to_dict(self):
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
    block_number: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    miner: str
    merkle_root: str
    nonce: int = 0
    difficulty: int = 4

    def calculate_hash(self) -> str:
        block_data = {
            "block_number": self.block_number,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "miner": self.miner,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce
        }
        return hashlib.sha256(json.dumps(block_data, sort_keys=True).encode()).hexdigest()

    def mine_block(self):
        target = "0" * self.difficulty
        while not self.calculate_hash().startswith(target):
            self.nonce += 1

class VirtualLedger:
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.balances: Dict[str, float] = {"nuclear-intelligence": 1000000.0}
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis = Block(0, time.time(), [], "0", "genesis", hashlib.sha256(b"").hexdigest())
        genesis.mine_block()
        self.chain.append(genesis)

    def add_transaction(self, tx_type, data, sender, receiver, amount=0.0):
        tx_id = hashlib.md5(f"{sender}{receiver}{time.time()}".encode()).hexdigest()[:16]
        tx = Transaction(tx_id, tx_type, time.time(), data, sender, receiver, amount, len(self.pending_transactions))
        self.pending_transactions.append(tx)
        return tx_id

    def mint_nes_token(self, answer_id, question, answer, evaluation_scores, answer_metadata):
        token_data = {
            "token_type": "NES",
            "token_value": 1.0,
            "answer_id": answer_id,
            "question": question[:500],
            "answer_hash": hashlib.sha256(answer.encode()).hexdigest(),
            "evaluation_scores": evaluation_scores,
            "timestamp": datetime.now().isoformat()
        }
        tx_id = self.add_transaction(TransactionType.NES_MINT, token_data, "nuclear-intelligence", answer_id, 1.0)
        self.balances[answer_id] = self.balances.get(answer_id, 0.0) + 1.0
        return {"tx_id": tx_id, "token_data": token_data}

    def mine_pending_block(self):
        if not self.pending_transactions: return None
        last_block = self.chain[-1]
        new_block = Block(len(self.chain), time.time(), self.pending_transactions.copy(), 
                          last_block.calculate_hash(), "nuclear-intelligence", "root")
        new_block.mine_block()
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

# ==================== Core Intelligence ====================

class NuclearIntelligenceCore:
    def __init__(self, api_key):
        self.client = AsyncOpenAI(api_key=api_key)
        self.knowledge_base = {}
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = faiss.IndexFlatL2(384)
        self.docs = []

    async def _call_llm(self, prompt):
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content

    async def generate_complex_questions(self, num=3):
        prompt = f"Generate {num} complex nuclear energy research questions in JSON format: {{'questions': [{{'question': str, 'category': str, 'complexity': int, 'keywords': [str]}}]}}"
        res = await self._call_llm(prompt)
        data = json.loads(res)
        questions = []
        for q in data['questions']:
            questions.append(ResearchQuestion(hashlib.md5(q['question'].encode()).hexdigest()[:12], 
                                             q['question'], ResearchCategory(q.get('category', 'physics')), 
                                             q.get('complexity', 7), datetime.now(), q.get('keywords', [])))
        return questions

    async def conduct_deep_research(self, question: ResearchQuestion):
        prompt = f"Research this nuclear question: {question.question}. Provide JSON: {{'answer': str, 'sources': [{{'title': str, 'url': str}}], 'equations': [str], 'examples': [str], 'citations': [str]}}"
        res = await self._call_llm(prompt)
        data = json.loads(res)
        return ResearchAnswer(hashlib.md5(f"{question.id}{time.time()}".encode()).hexdigest()[:12],
                             question.id, data['answer'], data.get('sources', []), data.get('equations', []),
                             data.get('examples', []), data.get('citations', []), datetime.now(), "gpt-4-turbo",
                             EvaluationScore(0,0,0,0,0))

    async def evaluate_answer(self, answer: ResearchAnswer):
        prompt = f"Evaluate this answer: {answer.answer[:1000]}. Provide JSON scores 0-100: {{'scientific_accuracy': int, 'novelty_score': int, 'usefulness_score': int, 'self_consistency': int, 'overall_score': int}}"
        res = await self._call_llm(prompt)
        data = json.loads(res)
        return EvaluationScore(**data)

    def add_to_knowledge_base(self, answer: ResearchAnswer):
        self.knowledge_base[answer.id] = asdict(answer)
        emb = self.embedding_model.encode(answer.answer).astype('float32')
        self.index.add(np.array([emb]))
        self.docs.append(answer.answer)

# ==================== UI ====================

core = None
ledger = VirtualLedger()

async def run_cycle(api_key):
    global core
    if not core: core = NuclearIntelligenceCore(api_key)
    
    questions = await core.generate_complex_questions(1)
    results = []
    for q in questions:
        ans = await core.conduct_deep_research(q)
        score = await core.evaluate_answer(ans)
        ans.evaluation_scores = score
        
        if score.scientific_accuracy >= 93:
            mint = ledger.mint_nes_token(ans.id, q.question, ans.answer, score.dict(), asdict(ans))
            core.add_to_knowledge_base(ans)
            results.append(f"✅ Minted NES for: {q.question[:50]}... (Score: {score.overall_score})")
        else:
            results.append(f"❌ Failed Accuracy: {q.question[:50]}... (Score: {score.scientific_accuracy})")
    
    ledger.mine_pending_block()
    return "\n".join(results), f"Total NES: {sum(ledger.balances.values()) - 1000000.0}"

def ui_run(api_key):
    return asyncio.run(run_cycle(api_key))

with gr.Blocks(title="Nuclear Intelligence") as demo:
    gr.Markdown("# ⚛️ Nuclear Intelligence System v2.0")
    with gr.Row():
        key_input = gr.Textbox(label="OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        run_btn = gr.Button("Execute Research Cycle")
    
    with gr.Row():
        output = gr.Textbox(label="Cycle Output", lines=10)
        stats = gr.Label(label="NES Tokens Minted")
    
    run_btn.click(ui_run, inputs=[key_input], outputs=[output, stats])

if __name__ == "__main__":
    demo.launch()
