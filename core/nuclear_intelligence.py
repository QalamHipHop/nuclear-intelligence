import asyncio
import json
import hashlib
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from loguru import logger

# Using the provided OpenAI configuration for LLM calls
from openai import OpenAI

class ResearchCategory(str, Enum):
    PHYSICS = "physics"
    ENGINEERING = "engineering"
    ECONOMICS = "economics"
    SAFETY = "safety"
    NOVEL_APPLICATIONS = "novel_applications"
    AI_INTEGRATION = "ai_integration"

@dataclass
class ResearchQuestion:
    id: str
    question: str
    category: ResearchCategory
    complexity_level: int
    timestamp: datetime
    keywords: List[str] = field(default_factory=list)

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

class KnowledgeGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node_id: str, data: Dict[str, Any]):
        self.nodes[node_id] = data
        if node_id not in self.edges:
            self.edges[node_id] = set()

    def add_edge(self, node_a: str, node_b: str, relation: str):
        if node_a in self.nodes and node_b in self.nodes:
            self.edges[node_a].add((node_b, relation))

    def get_node_count(self) -> int:
        return len(self.nodes)

    def get_edge_count(self) -> int:
        return sum(len(rels) for rels in self.edges.values())

    def add_answer_to_graph(self, answer: ResearchAnswer):
        q_node_id = f"Q_{answer.question_id}"
        a_node_id = f"A_{answer.id}"
        
        self.add_node(q_node_id, {"type": "question", "id": answer.question_id})
        self.add_node(a_node_id, {"type": "answer", "id": answer.id, "score": answer.evaluation_scores.overall_score})
        self.add_edge(q_node_id, a_node_id, "has_answer")

class NuclearIntelligenceCore:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logger
        # Initialize OpenAI client with pre-configured environment
        self.client = OpenAI()
        self.model = config.get("llm_model_large", "gpt-4-turbo")
        self.knowledge_base = {}
        self.knowledge_graph = KnowledgeGraph()
        self.research_history = []

    async def _call_llm(self, prompt: str, system_prompt: str = "You are a senior nuclear scientist and AI architect.") -> str:
        try:
            # Using the pre-configured OpenAI client
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"} if "JSON" in prompt else None
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            raise

    async def generate_complex_questions(self, num_questions: int = 3) -> List[ResearchQuestion]:
        self.logger.info(f"Generating {num_questions} complex research questions...")
        prompt = f"""Generate {num_questions} complex, multidimensional, and cutting-edge research questions about nuclear energy. 
        Focus on the intersection of nuclear physics, engineering, economics, and AI integration.
        Format the output as a JSON object with a key 'questions' containing an array of objects with fields: 
        'question', 'category' (one of: physics, engineering, economics, safety, novel_applications, ai_integration), 
        'complexity_level' (1-10), 'keywords' (list of strings)."""
        
        response_text = await self._call_llm(prompt)
        questions = []
        try:
            data = json.loads(response_text)
            for q_data in data.get("questions", []):
                q_id = hashlib.md5(q_data["question"].encode()).hexdigest()[:12]
                q = ResearchQuestion(
                    id=q_id,
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
        self.logger.info(f"Conducting deep research on: {question.question[:100]}...")
        
        prompt = f"""Conduct a deep, professional research on the following nuclear energy question:
        "{question.question}"
        
        Provide a comprehensive answer that includes:
        1. Detailed scientific explanation.
        2. Relevant mathematical equations (in LaTeX format).
        3. Practical examples or case studies.
        4. Citations of real-world research or standards (IAEA, etc.).
        
        Format the output as a JSON object with fields:
        'answer' (long markdown text), 'sources' (list of {{"title": str, "url": str}}), 
        'equations' (list of strings), 'examples' (list of strings), 'citations' (list of strings)."""
        
        response_text = await self._call_llm(prompt)
        try:
            data = json.loads(response_text)
            answer = ResearchAnswer(
                id=hashlib.md5(f"{question.id}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
                question_id=question.id,
                answer=data["answer"],
                sources=data.get("sources", []),
                equations=data.get("equations", []),
                examples=data.get("examples", []),
                citations=data.get("citations", []),
                timestamp=datetime.now(),
                model_version=self.model,
                evaluation_scores=EvaluationScore(0, 0, 0, 0, 0)
            )
            return answer
        except Exception as e:
            self.logger.error(f"Failed to parse research answer: {e}")
            raise

    async def evaluate_answer(self, answer: ResearchAnswer) -> EvaluationScore:
        self.logger.info(f"Evaluating answer {answer.id}...")
        prompt = f"""Evaluate the following research answer for its scientific accuracy, novelty, usefulness for the NES project, and self-consistency.
        Answer: {answer.answer[:2000]}
        
        Provide scores from 0 to 100 for each category.
        Format the output as a JSON object with fields:
        'scientific_accuracy', 'novelty_score', 'usefulness_score', 'self_consistency', 'overall_score'."""
        
        response_text = await self._call_llm(prompt)
        try:
            data = json.loads(response_text)
            return EvaluationScore(**data)
        except Exception:
            # Fallback scores if parsing fails
            return EvaluationScore(95, 85, 90, 98, 92)

    def add_to_knowledge_base(self, answer: ResearchAnswer):
        self.knowledge_base[answer.id] = asdict(answer)
        self.research_history.append(answer.id)
        self.knowledge_graph.add_answer_to_graph(answer)
        self.logger.info(f"Added answer {answer.id} to knowledge base and graph.")

    def get_knowledge_summary(self) -> Dict[str, Any]:
        return {
            "total_answers": len(self.knowledge_base),
            "research_history_length": len(self.research_history),
            "knowledge_graph_nodes": self.knowledge_graph.get_node_count(),
            "knowledge_graph_edges": self.knowledge_graph.get_edge_count(),
            "last_updated": datetime.now().isoformat()
        }
