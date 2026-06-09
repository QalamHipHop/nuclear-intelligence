"""
Nuclear Intelligence System v2.0 - Complete Implementation
Autonomous AI-powered nuclear energy research with blockchain tokenization
"""

import gradio as gr
import asyncio
import json
import hashlib
import hmac
import time
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path

# Third-party imports
from openai import AsyncOpenAI
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

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
        return {
            'scientific_accuracy': self.scientific_accuracy,
            'novelty_score': self.novelty_score,
            'usefulness_score': self.usefulness_score,
            'self_consistency': self.self_consistency,
            'overall_score': self.overall_score
        }

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
    sources: List[Dict[str, str]] = field(default_factory=list)
    equations: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    model_version: str = "gpt-4-turbo"
    evaluation_scores: Optional[EvaluationScore] = None

# ==================== Blockchain Components ====================

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
    transactions: List[Transaction] = field(default_factory=list)
    previous_hash: str = ""
    miner: str = "nuclear-intelligence"
    merkle_root: str = ""
    nonce: int = 0
    difficulty: int = 2

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
        current_hash = self.calculate_hash()
        while not current_hash.startswith(target):
            self.nonce += 1
            current_hash = self.calculate_hash()

class VirtualLedger:
    """Virtual Blockchain for NES Token Management"""
    
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.balances: Dict[str, float] = {"nuclear-intelligence": 1000000.0}
        self.transaction_history: List[Dict[str, Any]] = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis = Block(
            block_number=0,
            timestamp=time.time(),
            previous_hash="0",
            merkle_root=hashlib.sha256(b"").hexdigest()
        )
        genesis.mine_block()
        self.chain.append(genesis)

    def add_transaction(self, tx_type: TransactionType, data: Dict, sender: str, receiver: str, amount: float = 0.0) -> str:
        tx_id = hashlib.md5(f"{sender}{receiver}{time.time()}".encode()).hexdigest()[:16]
        tx = Transaction(
            tx_id=tx_id,
            tx_type=tx_type,
            timestamp=time.time(),
            data=data,
            sender=sender,
            receiver=receiver,
            amount=amount,
            nonce=len(self.pending_transactions)
        )
        self.pending_transactions.append(tx)
        return tx_id

    def mint_nes_token(self, answer_id: str, question: str, answer: str, evaluation_scores: Dict, answer_metadata: Dict) -> Dict:
        token_data = {
            "token_type": "NES",
            "token_value": 1.0,
            "answer_id": answer_id,
            "question": question[:500],
            "answer_hash": hashlib.sha256(answer.encode()).hexdigest(),
            "evaluation_scores": evaluation_scores,
            "timestamp": datetime.now().isoformat()
        }
        tx_id = self.add_transaction(
            TransactionType.NES_MINT,
            token_data,
            "nuclear-intelligence",
            answer_id,
            1.0
        )
        self.balances[answer_id] = self.balances.get(answer_id, 0.0) + 1.0
        return {"tx_id": tx_id, "token_data": token_data}

    def mine_pending_block(self) -> Optional[Block]:
        if not self.pending_transactions:
            return None
        last_block = self.chain[-1]
        new_block = Block(
            block_number=len(self.chain),
            timestamp=time.time(),
            transactions=self.pending_transactions.copy(),
            previous_hash=last_block.calculate_hash(),
            merkle_root=hashlib.sha256(b"").hexdigest()
        )
        new_block.mine_block()
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

    def get_total_nes_minted(self) -> float:
        return sum(self.balances.values()) - 1000000.0

# ==================== Nuclear Intelligence Core ====================

class NuclearIntelligenceCore:
    """Core AI Engine for Nuclear Energy Research"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.knowledge_base: Dict[str, Any] = {}
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = faiss.IndexFlatL2(384)
        self.docs: List[str] = []

    async def _call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def generate_complex_questions(self, num: int = 3) -> List[ResearchQuestion]:
        prompt = f"""Generate {num} complex, multidimensional nuclear energy research questions.
        Return JSON: {{"questions": [{{"question": "str", "category": "physics|engineering|economics|safety|novel_applications|ai_integration", "complexity": 1-10, "keywords": ["str"]}}]}}"""
        
        try:
            res = await self._call_llm(prompt, temperature=0.8)
            data = json.loads(res)
            questions = []
            for q in data.get('questions', []):
                q_id = hashlib.md5(q['question'].encode()).hexdigest()[:12]
                questions.append(ResearchQuestion(
                    id=q_id,
                    question=q['question'],
                    category=ResearchCategory(q.get('category', 'physics')),
                    complexity_level=q.get('complexity', 7),
                    timestamp=datetime.now(),
                    keywords=q.get('keywords', [])
                ))
            return questions
        except:
            return []

    async def conduct_deep_research(self, question: ResearchQuestion) -> ResearchAnswer:
        prompt = f"""Research this nuclear question: {question.question}
        Return JSON: {{"answer": "detailed answer", "sources": [{{"title": "str", "url": "str"}}], "equations": ["str"], "examples": ["str"], "citations": ["str"]}}"""
        
        try:
            res = await self._call_llm(prompt, temperature=0.6)
            data = json.loads(res)
            return ResearchAnswer(
                id=hashlib.md5(f"{question.id}{time.time()}".encode()).hexdigest()[:12],
                question_id=question.id,
                answer=data.get('answer', 'No answer generated'),
                sources=data.get('sources', []),
                equations=data.get('equations', []),
                examples=data.get('examples', []),
                citations=data.get('citations', [])
            )
        except:
            return ResearchAnswer(
                id=hashlib.md5(f"{question.id}{time.time()}".encode()).hexdigest()[:12],
                question_id=question.id,
                answer="Error in research"
            )

    async def evaluate_answer(self, answer: ResearchAnswer) -> EvaluationScore:
        prompt = f"""Evaluate this nuclear research answer: {answer.answer[:500]}
        Return JSON with scores 0-100: {{"scientific_accuracy": int, "novelty_score": int, "usefulness_score": int, "self_consistency": int, "overall_score": int}}"""
        
        try:
            res = await self._call_llm(prompt, temperature=0.5)
            data = json.loads(res)
            return EvaluationScore(
                scientific_accuracy=float(data.get('scientific_accuracy', 85)),
                novelty_score=float(data.get('novelty_score', 80)),
                usefulness_score=float(data.get('usefulness_score', 85)),
                self_consistency=float(data.get('self_consistency', 90)),
                overall_score=float(data.get('overall_score', 85))
            )
        except:
            return EvaluationScore(85, 80, 85, 90, 85)

    def add_to_knowledge_base(self, answer: ResearchAnswer):
        self.knowledge_base[answer.id] = asdict(answer)
        try:
            emb = self.embedding_model.encode(answer.answer).astype('float32')
            self.index.add(np.array([emb]))
            self.docs.append(answer.answer)
        except:
            pass

# ==================== Global State ====================

core: Optional[NuclearIntelligenceCore] = None
ledger = VirtualLedger()

async def execute_research_cycle(api_key: str) -> tuple:
    """Execute a complete research cycle"""
    global core
    
    if not api_key or api_key == "":
        return "❌ Error: Please provide OpenAI API Key", "0 NES"
    
    if not core:
        core = NuclearIntelligenceCore(api_key)
    
    try:
        # Generate questions
        questions = await core.generate_complex_questions(1)
        if not questions:
            return "❌ Failed to generate questions", "0 NES"
        
        results = []
        for q in questions:
            # Conduct research
            ans = await core.conduct_deep_research(q)
            
            # Evaluate answer
            score = await core.evaluate_answer(ans)
            ans.evaluation_scores = score
            
            # Mint token if criteria met
            if score.scientific_accuracy >= 93:
                mint = ledger.mint_nes_token(
                    ans.id,
                    q.question,
                    ans.answer,
                    score.dict(),
                    asdict(ans)
                )
                core.add_to_knowledge_base(ans)
                results.append(f"✅ Minted NES Token\n   Question: {q.question[:60]}...\n   Score: {score.overall_score:.1f}%")
            else:
                results.append(f"⚠️  Low Accuracy: {q.question[:60]}...\n   Score: {score.scientific_accuracy:.1f}%")
        
        # Mine block
        ledger.mine_pending_block()
        
        output = "\n\n".join(results) if results else "No tokens minted"
        total_nes = ledger.get_total_nes_minted()
        
        return output, f"{total_nes:.1f} NES Minted"
    
    except Exception as e:
        return f"❌ Error: {str(e)}", "0 NES"

def ui_execute(api_key: str) -> tuple:
    """Wrapper for Gradio"""
    return asyncio.run(execute_research_cycle(api_key))

# ==================== Gradio UI ====================

def create_ui():
    with gr.Blocks(title="Nuclear Intelligence v2.0", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # ⚛️ Nuclear Intelligence System v2.0
        
        **Advanced AI-powered autonomous nuclear energy research with blockchain tokenization**
        
        - 🤖 Autonomous question generation and deep research
        - 🧪 Multi-layer scientific evaluation
        - 🪙 NES token minting for validated knowledge
        - ⛓️ Blockchain-based immutable records
        - 🔬 Integration with OpenAI GPT-4 Turbo
        """)
        
        with gr.Row():
            api_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                value=os.getenv("OPENAI_API_KEY", ""),
                placeholder="sk-..."
            )
            run_btn = gr.Button("▶️ Execute Research Cycle", size="lg", variant="primary")
        
        with gr.Row():
            output = gr.Textbox(
                label="Research Results",
                lines=12,
                interactive=False
            )
            stats = gr.Textbox(
                label="NES Token Statistics",
                lines=12,
                interactive=False
            )
        
        def update_stats():
            total = ledger.get_total_nes_minted()
            chain_len = len(ledger.chain)
            pending = len(ledger.pending_transactions)
            
            stats_text = f"""
**Blockchain State:**
- Chain Length: {chain_len}
- Total NES Minted: {total:.1f}
- Pending Transactions: {pending}
- Knowledge Base Size: {len(core.knowledge_base) if core else 0}

**System Status:**
- Status: Running
- Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            return stats_text
        
        def on_click(key):
            result, nes = ui_execute(key)
            stats_text = update_stats()
            return result, stats_text
        
        run_btn.click(on_click, inputs=[api_key], outputs=[output, stats])
        demo.load(update_stats, outputs=[stats])
    
    return demo

if __name__ == "__main__":
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
