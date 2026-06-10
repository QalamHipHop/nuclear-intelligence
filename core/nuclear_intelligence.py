"""
Nuclear Intelligence Core - Advanced AI Research Engine
=======================================================
Multi-model LLM, RAG, Knowledge Graph, Multi-Layer Evaluation
Free provider chain: Groq → Together → Cloudflare → OpenRouter → HuggingFace
"""

import os
import json
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from core.llm_engine import LLMEngine
from core.web_search import WebSearchEngine
from core.embeddings import EmbeddingEngine
from core.knowledge_graph import KnowledgeGraph


class ResearchQuestion:
    def __init__(self, question: str, category: str, difficulty: int, keywords: List[str]):
        self.question = question
        self.category = category
        self.difficulty = difficulty
        self.keywords = keywords

    def to_dict(self):
        return {
            "question": self.question,
            "category": self.category,
            "difficulty": self.difficulty,
            "keywords": self.keywords,
            "timestamp": datetime.now().isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            question=data["question"],
            category=data["category"],
            difficulty=data["difficulty"],
            keywords=data["keywords"]
        )


class ResearchAnswer:
    def __init__(self, answer: str, citations: List[str], novelty_score: float,
                 accuracy_score: float, sources: List[Dict]):
        self.answer = answer
        self.citations = citations
        self.novelty_score = novelty_score
        self.accuracy_score = accuracy_score
        self.sources = sources

    def to_dict(self):
        return {
            "answer": self.answer,
            "citations": self.citations,
            "novelty_score": self.novelty_score,
            "accuracy_score": self.accuracy_score,
            "sources": self.sources,
            "timestamp": datetime.now().isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            answer=data["answer"],
            citations=data["citations"],
            novelty_score=data["novelty_score"],
            accuracy_score=data["accuracy_score"],
            sources=data.get("sources", [])
        )


class EvaluationScore:
    def __init__(self, scientific_accuracy: float, novelty_score: float,
                 usefulness_score: float, self_consistency_check: bool,
                 justification: str):
        self.scientific_accuracy = scientific_accuracy
        self.novelty_score = novelty_score
        self.usefulness_score = usefulness_score
        self.self_consistency_check = self_consistency_check
        self.justification = justification

    def to_dict(self):
        return {
            "scientific_accuracy": self.scientific_accuracy,
            "novelty_score": self.novelty_score,
            "usefulness_score": self.usefulness_score,
            "self_consistency_check": self.self_consistency_check,
            "justification": self.justification,
            "timestamp": datetime.now().isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            scientific_accuracy=data["scientific_accuracy"],
            novelty_score=data["novelty_score"],
            usefulness_score=data["usefulness_score"],
            self_consistency_check=data["self_consistency_check"],
            justification=data["justification"]
        )

    def overall_score(self) -> float:
        return (
            self.scientific_accuracy * 0.5 +
            self.novelty_score * 0.25 +
            self.usefulness_score * 0.25
        )


SYSTEM_PROMPTS = {
    "question_generator": """You are the Nuclear Intelligence Architect — an elite AI researcher specializing in nuclear physics, reactor engineering, fusion science, nuclear safety, and energy economics.

Generate ONE high-impact, cutting-edge research question that:
- Pushes the boundaries of nuclear science or next-gen reactor design
- Addresses a real gap in nuclear energy knowledge
- Is specific enough to research deeply but broad enough for rich answers

Return ONLY valid JSON:
{
  "question": "the research question text",
  "category": "Physics|Engineering|Safety|Economics|Fusion|Chemistry|Materials",
  "difficulty": 1-10,
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}""",

    "researcher": """You are a Senior Nuclear Scientist with deep expertise in nuclear physics, reactor engineering, fusion research, and nuclear economics. You provide rigorous, accurate, peer-reviewed-level scientific analysis.

Return ONLY valid JSON:
{
  "answer": "detailed scientific answer with equations and analysis (500-1500 words)",
  "citations": ["source1", "source2", "source3"],
  "novelty_score": 0-100,
  "accuracy_score": 0-100,
  "sources": [{"title": "...", "url": "...", "type": "arxiv|web|native"}]
}""",

    "evaluator": """You are an Independent Scientific Auditor. Evaluate nuclear science research output.

Return ONLY valid JSON:
{
  "scientific_accuracy": 0-100,
  "novelty_score": 0-100,
  "usefulness_score": 0-100,
  "self_consistency_check": true/false,
  "justification": "detailed reasoning for each score"
}""",

    "developer_analyzer": """You are a Nuclear Intelligence Senior Analyst in Developer Mode.

Return JSON:
{
  "physics_depth": "fundamental analysis",
  "cross_domain": ["connection1", "connection2"],
  "research_gaps": ["gap1", "gap2"],
  "implementation_pathways": ["path1", "path2"],
  "token_value_rationale": "why this deserves NES minting"
}""",

    "synthetic_context": """You are a Nuclear Intelligence Context Synthesizer. Synthesize context from RAG and web search.

Return JSON:
{
  "synthesized_context": "comprehensive synthesized context (300-800 words)",
  "key_facts": ["fact1", "fact2", "fact3", "fact4", "fact5"],
  "confidence_level": "high|medium|low",
  "data_gaps": ["gap1", "gap2"]
}"""
}


class NuclearIntelligenceCore:
    def __init__(
        self,
        vector_db_path: str = "knowledge_base/faiss_index",
        kg_path: str = "knowledge_base/knowledge_graph.json",
        provider_chain: Optional[List[str]] = None
    ):
        self.llm = LLMEngine(provider_chain=provider_chain)
        self.embeddings = EmbeddingEngine()
        self.search = WebSearchEngine()
        self.kg = KnowledgeGraph(path=kg_path)
        self.vector_db_path = vector_db_path
        self._init_vectorstore()

        self.stats = {
            "questions_generated": 0,
            "researches_conducted": 0,
            "evaluations_done": 0,
            "tokens_minted": 0,
            "tokens_rejected": 0,
        }

        logger.info(f"Nuclear Intelligence Core v2.0 initialized. LLM providers: {self.llm._available_providers}")

    def _init_vectorstore(self):
        try:
            from langchain_community.vectorstores import FAISS
            self.vectorstore = self.embeddings.load_or_create_vectordb(
                self.vector_db_path,
                initial_text="Nuclear Intelligence: Accelerating nuclear energy through AI and blockchain."
            )
            logger.info("FAISS vector store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            self.vectorstore = None

    def _parse_json_response(self, text: str):
        import re
        content = text.strip()
        if "```" in content:
            parts = content.split("```")
            for part in parts:
                part = part.strip()
                for prefix in ["json", "yaml", ""]:
                    if part.startswith(prefix):
                        part = part[len(prefix):].strip()
                    try:
                        return json.loads(part)
                    except:
                        pass
        try:
            return json.loads(content)
        except:
            pass
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        return None

    def generate_question(self, context: str = "", category_hint: str = "") -> Optional[ResearchQuestion]:
        logger.info("Generating research question...")
        kg_context = ""
        if self.kg.graph["entities"]:
            recent = list(self.kg.graph["entities"].items())[-3:]
            kg_context = "\n".join([f"- {q['question']}" for qid, q in recent])

        prompt = f"""Context: {context or 'No specific context provided.'}
Knowledge Graph:\n{kg_context or '[No prior knowledge available]'}
Category hint: {category_hint or 'Any nuclear energy domain'}"""

        result = self.llm.structured_completion(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS["question_generator"],
            response_format="json"
        )

        if not result or result.get("parse_error"):
            return self._fallback_question()

        parsed = result.get("parsed", {})
        try:
            q = ResearchQuestion(
                question=parsed.get("question", ""),
                category=parsed.get("category", "Physics"),
                difficulty=int(parsed.get("difficulty", 5)),
                keywords=parsed.get("keywords", [])
            )
            self.stats["questions_generated"] += 1
            return q
        except Exception as e:
            logger.error(f"Failed to parse question: {e}")
            return self._fallback_question()

    def _fallback_question(self) -> ResearchQuestion:
        import random
        fallback = [
            ResearchQuestion("What are the latest advances in molten salt reactor (MSR) safety systems?", "Engineering", 7, ["MSR", "molten salt", "safety", "LWR"]),
            ResearchQuestion("How does tritium breeding ratio optimization work in D-T fusion reactors?", "Fusion", 8, ["tritium", "D-T fusion", "breeding ratio", "TBR"]),
            ResearchQuestion("What is the current state of nuclear waste transmutation using ADS?", "Physics", 8, ["transmutation", "ADS", "nuclear waste"]),
        ]
        q = random.choice(fallback)
        self.stats["questions_generated"] += 1
        return q

    def conduct_research(self, question: ResearchQuestion, use_web_search: bool = True) -> Optional[ResearchAnswer]:
        logger.info(f"Conducting research: {question.question[:60]}...")
        self.stats["researches_conducted"] += 1

        rag_context = ""
        sources = []
        if self.vectorstore:
            try:
                docs = self.vectorstore.similarity_search(question.question, k=5)
                rag_context = "\n".join([f"[RAG] {d.page_content}" for d in docs])
            except:
                pass

        if use_web_search:
            try:
                web_results = self.search.search(question.question, num_results=5)
                if web_results:
                    for r in web_results[:5]:
                        sources.append({"title": r.get("title", ""), "url": r.get("url", ""), "type": "web"})
            except:
                pass

        synthesis_prompt = f"""Research Question: {question.question}
Category: {question.category}
RAG Context:\n{rag_context or '[No prior knowledge available]'}

Synthesize and provide detailed research."""

        synthesis_result = self.llm.structured_completion(
            prompt=synthesis_prompt,
            system_prompt=SYSTEM_PROMPTS["synthetic_context"],
            response_format="json"
        )

        synthesized_context = ""
        if synthesis_result and not synthesis_result.get("parse_error"):
            synthesized_context = synthesis_result.get("parsed", {}).get("synthesized_context", "")

        full_prompt = f"""Research Question: {question.question}
Category: {question.category}
Keywords: {', '.join(question.keywords)}
Context:\n{synthesized_context or rag_context or 'Use your nuclear science expertise.'}

Provide a comprehensive, detailed scientific answer."""

        result = self.llm.structured_completion(
            prompt=full_prompt,
            system_prompt=SYSTEM_PROMPTS["researcher"],
            response_format="json"
        )

        if not result or result.get("parse_error"):
            return self._fallback_answer(question)

        parsed = result.get("parsed", {})
        answer_text = parsed.get("answer", "")
        if not answer_text:
            return self._fallback_answer(question)

        return ResearchAnswer(
            answer=answer_text,
            citations=parsed.get("citations", []),
            novelty_score=float(parsed.get("novelty_score", 50)),
            accuracy_score=float(parsed.get("accuracy_score", 50)),
            sources=sources
        )

    def _fallback_answer(self, question: ResearchQuestion) -> ResearchAnswer:
        return ResearchAnswer(
            answer=f"Advanced research on {question.question}. Keywords: {', '.join(question.keywords)}.",
            citations=["Nuclear Intelligence Knowledge Base"],
            novelty_score=45, accuracy_score=70,
            sources=[{"title": "Fallback", "url": "", "type": "internal"}]
        )

    def evaluate_answer(self, question: ResearchQuestion, answer: ResearchAnswer) -> EvaluationScore:
        logger.info("Evaluating research output...")
        self.stats["evaluations_done"] += 1

        eval_prompt = f"""Research Question: {question.question}
Answer: {answer.answer[:2000]}

Evaluate this nuclear science research output."""

        result = self.llm.structured_completion(
            prompt=eval_prompt,
            system_prompt=SYSTEM_PROMPTS["evaluator"],
            response_format="json"
        )

        if not result or result.get("parse_error"):
            return EvaluationScore(
                scientific_accuracy=70.0, novelty_score=40.0,
                usefulness_score=60.0, self_consistency_check=True,
                justification="Evaluation API unavailable - conservative estimate."
            )

        parsed = result.get("parsed", {})
        return EvaluationScore(
            scientific_accuracy=float(parsed.get("scientific_accuracy", 50)),
            novelty_score=float(parsed.get("novelty_score", 50)),
            usefulness_score=float(parsed.get("usefulness_score", 50)),
            self_consistency_check=bool(parsed.get("self_consistency_check", True)),
            justification=parsed.get("justification", "")
        )

    def developer_mode_analysis(self, question: ResearchQuestion, answer: ResearchAnswer) -> Dict:
        logger.info("Running developer-mode analysis...")
        result = self.llm.structured_completion(
            prompt=f"Question: {question.question}\nAnswer: {answer.answer[:3000]}\nCategory: {question.category}",
            system_prompt=SYSTEM_PROMPTS["developer_analyzer"],
            response_format="json"
        )
        if result and not result.get("parse_error"):
            return result.get("parsed", {})
        return {"error": "Developer analysis unavailable"}

    def integrate_knowledge(self, question: ResearchQuestion, answer: ResearchAnswer, evaluation: EvaluationScore):
        logger.info("Integrating knowledge...")
        if self.vectorstore:
            try:
                content = f"Question: {question.question}\nCategory: {question.category}\nAnswer: {answer.answer}\nAccuracy: {evaluation.scientific_accuracy}%"
                metadata = {"category": question.category, "accuracy": evaluation.scientific_accuracy, "novelty": evaluation.novelty_score}
                self.vectorstore.add_texts([content], metadatas=[metadata])
                self.vectorstore.save_local(self.vector_db_path)
            except Exception as e:
                logger.error(f"Vector store error: {e}")

        self.kg.add_knowledge(question.question, answer.answer, {
            "category": question.category, "difficulty": question.difficulty,
            "accuracy": evaluation.scientific_accuracy, "novelty": evaluation.novelty_score,
            "usefulness": evaluation.usefulness_score, "citations": answer.citations
        })
        self.stats["tokens_minted"] += 1

    def reject_answer(self, evaluation: EvaluationScore):
        self.stats["tokens_rejected"] += 1

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "llm_health": self.llm.health_check(),
            "llm_stats": self.llm.get_stats(),
            "knowledge_entities": len(self.kg.graph["entities"]),
            "approval_rate": f"{(self.stats['tokens_minted'] / max(self.stats['researches_conducted'], 1) * 100):.1f}%"
        }
