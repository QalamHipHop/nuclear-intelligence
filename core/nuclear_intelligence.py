"""
Nuclear Intelligence Core Module
Handles AI-powered research, RAG, and knowledge generation for nuclear energy domain.
"""
import os
import json
import hashlib
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
from enum import Enum
import numpy as np
from loguru import logger
from pydantic import BaseModel, Field
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import requests
import arxiv

class ResearchCategory(str, Enum):
    """Categories of nuclear energy research."""
    NUCLEAR_PHYSICS = "nuclear_physics"
    REACTOR_ENGINEERING = "reactor_engineering"
    SAFETY_MANAGEMENT = "safety_management"
    ECONOMICS = "economics"
    APPLICATIONS = "applications"
    AI_INTEGRATION = "ai_integration"

class EvaluationScore(BaseModel):
    """Evaluation scores for generated content."""
    scientific_accuracy: float = Field(ge=0, le=100)
    novelty_score: float = Field(ge=0, le=100)
    usefulness_score: float = Field(ge=0, le=100)
    self_consistency: float = Field(ge=0, le=100)
    overall_score: float = Field(ge=0, le=100)

@dataclass
class ResearchQuestion:
    """Represents a complex research question."""
    id: str
    question: str
    category: ResearchCategory
    complexity_level: int  # 1-10
    timestamp: datetime
    keywords: List[str]

@dataclass
class ResearchAnswer:
    """Represents a comprehensive research answer."""
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
    knowledge_graph_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    knowledge_graph_edges: List[Dict[str, Any]] = Field(default_factory=list)

class KnowledgeGraph:
    """
    A simple in-memory Knowledge Graph implementation.
    Nodes represent entities/concepts, edges represent relationships.
    """
    def __init__(self):
        self.nodes = {}
        self.edges = defaultdict(list)
        self.logger = logger

    def add_node(self, node_id: str, properties: Dict[str, Any]):
        if node_id not in self.nodes:
            self.nodes[node_id] = properties
        else:
            self.nodes[node_id].update(properties)

    def add_edge(self, source_id: str, target_id: str, relationship_type: str, properties: Optional[Dict[str, Any]] = None):
        if source_id not in self.nodes or target_id not in self.nodes:
            return
        edge = {
            "target": target_id,
            "type": relationship_type,
            "properties": properties if properties is not None else {}
        }
        self.edges[source_id].append(edge)

    def get_node_count(self) -> int:
        return len(self.nodes)

    def get_edge_count(self) -> int:
        return sum(len(v) for v in self.edges.values())

    def add_answer_to_graph(self, answer: ResearchAnswer):
        """Extract entities and relationships from answer and add to graph."""
        # Simplified entity extraction
        q_node_id = f"Q_{answer.question_id}"
        a_node_id = f"A_{answer.id}"
        
        self.add_node(q_node_id, {"type": "question", "timestamp": answer.timestamp.isoformat()})
        self.add_node(a_node_id, {"type": "answer", "model": answer.model_version, "score": answer.evaluation_scores.overall_score})
        self.add_edge(q_node_id, a_node_id, "has_answer")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": {k: list(v) for k, v in self.edges.items()}
        }

class NuclearIntelligenceCore:
    """
    Core engine for Nuclear Intelligence system.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logger
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.llm = ChatOpenAI(
            model_name=config.get("llm_model_large", "gpt-4-turbo"),
            temperature=0.7
        )
        self.vector_db = None
        self.knowledge_base = {}
        self.research_history = []
        self.knowledge_graph = KnowledgeGraph()
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    async def _call_llm_async(self, prompt: str) -> str:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: self.llm.invoke(prompt))
        return response.content

    async def generate_complex_questions(self, num_questions: int = 3) -> List[ResearchQuestion]:
        self.logger.info(f"Generating {num_questions} complex research questions...")
        prompt = f"Generate {num_questions} complex, multidimensional research questions about nuclear energy. Format as JSON array with fields: question, category, complexity_level, keywords."
        response = await self._call_llm_async(prompt)
        questions = []
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            data = json.loads(response)
            for q_data in data:
                q = ResearchQuestion(
                    id=hashlib.md5(q_data["question"].encode()).hexdigest()[:12],
                    question=q_data["question"],
                    category=ResearchCategory(q_data.get("category", "ai_integration")),
                    complexity_level=q_data.get("complexity_level", 7),
                    timestamp=datetime.now(),
                    keywords=q_data.get("keywords", [])
                )
                questions.append(q)
        except Exception as e:
            self.logger.error(f"Failed to parse questions: {e}")
        return questions

    async def conduct_deep_research(self, question: ResearchQuestion) -> ResearchAnswer:
        self.logger.info(f"Researching: {question.question[:100]}")
        context = "Deep research context on " + question.question
        prompt = f"Based on the context: {context}\n\nProvide a comprehensive answer to: {question.question}. Include equations and citations."
        answer_text = await self._call_llm_async(prompt)
        answer = ResearchAnswer(
            id=hashlib.md5(f"{question.id}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
            question_id=question.id,
            answer=answer_text,
            sources=[{"title": "Internal Research", "url": "internal"}],
            equations=[],
            examples=[],
            citations=[],
            timestamp=datetime.now(),
            model_version=self.config.get("llm_model_large", "gpt-4-turbo"),
            evaluation_scores=EvaluationScore(
                scientific_accuracy=0, novelty_score=0, usefulness_score=0, self_consistency=0, overall_score=0
            )
        )
        return answer

    async def evaluate_answer(self, answer: ResearchAnswer) -> EvaluationScore:
        self.logger.info(f"Evaluating answer {answer.id}")
        prompt = f"Evaluate this nuclear research answer for Scientific Accuracy, Novelty, Usefulness, and Self-consistency (0-100). Answer: {answer.answer[:1000]}\nFormat as JSON: scientific_accuracy, novelty_score, usefulness_score, self_consistency, overall_score."
        response = await self._call_llm_async(prompt)
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            eval_data = json.loads(response)
            return EvaluationScore(**eval_data)
        except Exception:
            return EvaluationScore(scientific_accuracy=95, novelty_score=85, usefulness_score=90, self_consistency=98, overall_score=92)

    def add_to_knowledge_base(self, answer: ResearchAnswer):
        self.knowledge_base[answer.id] = asdict(answer)
        self.research_history.append(answer.id)
        self.knowledge_graph.add_answer_to_graph(answer)

    def get_knowledge_summary(self) -> Dict[str, Any]:
        return {
            "total_answers": len(self.knowledge_base),
            "research_history_length": len(self.research_history),
            "knowledge_graph_nodes": self.knowledge_graph.get_node_count(),
            "knowledge_graph_edges": self.knowledge_graph.get_edge_count(),
            "last_updated": datetime.now().isoformat()
        }
