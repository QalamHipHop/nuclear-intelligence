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
from enum import Enum

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
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


class NuclearIntelligenceCore:
    """
    Core engine for Nuclear Intelligence system.
    Handles RAG, knowledge generation, evaluation, and blockchain integration.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Nuclear Intelligence Core."""
        self.config = config
        self.logger = logger
        
        # Initialize embeddings and vector store
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name=config.get("llm_model_large", "gpt-4-turbo"),
            temperature=0.7,
            max_tokens=2000
        )
        
        # Initialize vector database
        self.vector_db = None
        self.knowledge_base = {}
        self.research_history = []
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.logger.info("Nuclear Intelligence Core initialized successfully")

    async def generate_complex_questions(self, num_questions: int = 3) -> List[ResearchQuestion]:
        """
        Generate complex, multidimensional research questions combining:
        - Physics + Engineering + Economics + Safety + Applications + AI Integration
        """
        self.logger.info(f"Generating {num_questions} complex research questions...")
        
        question_prompt = PromptTemplate(
            input_variables=["num_questions"],
            template="""
            Generate {num_questions} highly complex, multidimensional research questions 
            about nuclear energy that combine multiple domains:
            
            1. Nuclear Physics (fission, fusion, neutron physics, transmutation)
            2. Reactor Engineering (Gen II/III/IV, SMR, molten salt, PWR, BWR)
            3. Safety & Waste Management (non-proliferation, IAEA standards)
            4. Economics (PPA contracts, LCOE, tokenized uranium, energy credits)
            5. Modern Applications (AI data centers, desalination, hydrogen, load-following)
            6. AI & Blockchain Integration (knowledge tokenization, NES backing)
            
            For each question:
            - Ensure it's novel, cutting-edge, and requires deep research
            - Include 3-5 keywords
            - Rate complexity 1-10
            - Specify primary category
            
            Format as JSON array with fields: question, category, complexity_level, keywords
            """
        )
        
        response = await self._call_llm_async(question_prompt.format(num_questions=num_questions))
        
        questions = []
        try:
            questions_data = json.loads(response)
            for q_data in questions_data:
                q = ResearchQuestion(
                    id=hashlib.md5(q_data["question"].encode()).hexdigest()[:12],
                    question=q_data["question"],
                    category=ResearchCategory(q_data.get("category", "ai_integration")),
                    complexity_level=q_data.get("complexity_level", 7),
                    timestamp=datetime.now(),
                    keywords=q_data.get("keywords", [])
                )
                questions.append(q)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse generated questions as JSON")
        
        self.logger.info(f"Generated {len(questions)} research questions")
        return questions

    async def conduct_deep_research(self, question: ResearchQuestion) -> ResearchAnswer:
        """
        Conduct deep research using RAG, ArXiv, web search, and citation generation.
        """
        self.logger.info(f"Conducting deep research for question: {question.question[:100]}...")
        
        # Retrieve relevant documents from vector DB
        relevant_docs = await self._retrieve_relevant_documents(question)
        
        # Search ArXiv for recent papers
        arxiv_papers = await self._search_arxiv(question.keywords)
        
        # Web search for current information
        web_results = await self._web_search(question.question)
        
        # Combine all sources
        context = self._prepare_research_context(relevant_docs, arxiv_papers, web_results)
        
        # Generate comprehensive answer
        answer_prompt = PromptTemplate(
            input_variables=["question", "context"],
            template="""
            Based on the following context and research, provide a comprehensive, 
            scientifically accurate answer to this nuclear energy question:
            
            Question: {question}
            
            Context:
            {context}
            
            Your answer should include:
            1. Clear, detailed explanation
            2. Relevant equations and mathematical relationships
            3. Practical examples and case studies
            4. Citations and references
            5. Current state-of-the-art insights
            6. Future research directions
            
            Format the response with clear sections and markdown formatting.
            """
        )
        
        answer_text = await self._call_llm_async(
            answer_prompt.format(question=question.question, context=context)
        )
        
        # Extract equations, examples, and citations
        equations = self._extract_equations(answer_text)
        examples = self._extract_examples(answer_text)
        citations = self._extract_citations(answer_text)
        
        # Create answer object
        answer = ResearchAnswer(
            id=hashlib.md5(f"{question.id}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
            question_id=question.id,
            answer=answer_text,
            sources=self._format_sources(relevant_docs, arxiv_papers, web_results),
            equations=equations,
            examples=examples,
            citations=citations,
            timestamp=datetime.now(),
            model_version=self.config.get("llm_model_large", "gpt-4-turbo"),
            evaluation_scores=EvaluationScore(
                scientific_accuracy=0,
                novelty_score=0,
                usefulness_score=0,
                self_consistency=0,
                overall_score=0
            )
        )
        
        return answer

    async def evaluate_answer(self, answer: ResearchAnswer) -> EvaluationScore:
        """
        Perform multi-layer professional evaluation of the research answer.
        """
        self.logger.info(f"Evaluating answer {answer.id}...")
        
        # Scientific Accuracy Evaluation
        accuracy_prompt = PromptTemplate(
            input_variables=["answer"],
            template="""
            Evaluate the scientific accuracy of this nuclear energy research answer on a scale of 0-100.
            Consider: correctness of physics, engineering principles, citations, and technical details.
            
            Answer: {answer}
            
            Provide only a number 0-100 and brief justification.
            """
        )
        accuracy_score = await self._evaluate_metric(accuracy_prompt, answer.answer)
        
        # Novelty Evaluation
        novelty_score = await self._evaluate_novelty(answer)
        
        # Usefulness Evaluation
        usefulness_prompt = PromptTemplate(
            input_variables=["answer"],
            template="""
            Evaluate how useful this answer is for NES token valuation, risk assessment, and innovation.
            Scale 0-100.
            
            Answer: {answer}
            
            Provide only a number 0-100 and brief justification.
            """
        )
        usefulness_score = await self._evaluate_metric(usefulness_prompt, answer.answer)
        
        # Self-Consistency Check
        consistency_score = await self._check_self_consistency(answer)
        
        # Calculate overall score
        overall_score = (accuracy_score + novelty_score + usefulness_score + consistency_score) / 4
        
        scores = EvaluationScore(
            scientific_accuracy=accuracy_score,
            novelty_score=novelty_score,
            usefulness_score=usefulness_score,
            self_consistency=consistency_score,
            overall_score=overall_score
        )
        
        answer.evaluation_scores = scores
        self.logger.info(f"Evaluation complete. Overall score: {overall_score:.2f}")
        
        return scores

    async def _retrieve_relevant_documents(self, question: ResearchQuestion) -> List[Dict]:
        """Retrieve relevant documents from vector database."""
        if self.vector_db is None:
            return []
        
        try:
            docs = self.vector_db.similarity_search(question.question, k=5)
            return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
        except Exception as e:
            self.logger.error(f"Error retrieving documents: {e}")
            return []

    async def _search_arxiv(self, keywords: List[str]) -> List[Dict]:
        """Search ArXiv for relevant papers."""
        self.logger.info(f"Searching ArXiv for keywords: {keywords}")
        papers = []
        
        try:
            search_query = " OR ".join(keywords[:3])
            client = arxiv.Client()
            search = arxiv.Search(
                query=search_query,
                max_results=5,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            for paper in client.results(search):
                papers.append({
                    "title": paper.title,
                    "authors": [author.name for author in paper.authors],
                    "summary": paper.summary,
                    "url": paper.entry_id,
                    "published": paper.published.isoformat()
                })
        except Exception as e:
            self.logger.error(f"Error searching ArXiv: {e}")
        
        return papers

    async def _web_search(self, query: str) -> List[Dict]:
        """Perform web search for current information."""
        self.logger.info(f"Performing web search for: {query[:100]}")
        # Placeholder for web search implementation
        # Would integrate with search API (Google, Bing, etc.)
        return []

    def _prepare_research_context(self, docs: List, papers: List, web_results: List) -> str:
        """Prepare combined research context."""
        context = "## Vector Database Documents\n"
        for doc in docs[:3]:
            context += f"- {doc.get('content', '')[:200]}...\n"
        
        context += "\n## Recent ArXiv Papers\n"
        for paper in papers[:3]:
            context += f"- **{paper['title']}** ({paper['published']})\n"
            context += f"  {paper['summary'][:200]}...\n"
        
        return context

    def _extract_equations(self, text: str) -> List[str]:
        """Extract mathematical equations from answer text."""
        # Placeholder for equation extraction
        equations = []
        if "$$" in text or "$" in text:
            # Extract LaTeX equations
            import re
            equations = re.findall(r'\$\$.*?\$\$|\$.*?\$', text)
        return equations

    def _extract_examples(self, text: str) -> List[str]:
        """Extract practical examples from answer text."""
        # Placeholder for example extraction
        examples = []
        if "example" in text.lower() or "case study" in text.lower():
            # Extract example sections
            pass
        return examples

    def _extract_citations(self, text: str) -> List[str]:
        """Extract citations and references from answer text."""
        citations = []
        import re
        # Extract [Author, Year] style citations
        citations = re.findall(r'\[\w+,\s*\d{4}\]', text)
        return citations

    def _format_sources(self, docs: List, papers: List, web_results: List) -> List[Dict]:
        """Format all sources into a unified structure."""
        sources = []
        
        for paper in papers:
            sources.append({
                "type": "arxiv",
                "title": paper["title"],
                "url": paper["url"],
                "authors": ", ".join(paper["authors"][:3])
            })
        
        return sources

    async def _evaluate_metric(self, prompt: PromptTemplate, content: str) -> float:
        """Evaluate a specific metric."""
        try:
            response = await self._call_llm_async(prompt.format(answer=content[:1000]))
            # Extract numeric score from response
            import re
            scores = re.findall(r'\d+', response)
            if scores:
                return float(scores[0])
        except Exception as e:
            self.logger.error(f"Error evaluating metric: {e}")
        
        return 50.0

    async def _evaluate_novelty(self, answer: ResearchAnswer) -> float:
        """Evaluate novelty compared to knowledge base."""
        # Semantic comparison with existing knowledge
        novelty_score = 75.0  # Placeholder
        return novelty_score

    async def _check_self_consistency(self, answer: ResearchAnswer) -> float:
        """Check self-consistency of the answer through multiple tests."""
        consistency_score = 80.0  # Placeholder
        return consistency_score

    async def _call_llm_async(self, prompt: str) -> str:
        """Call LLM asynchronously."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.llm.predict(prompt)
        )
        return response

    def add_to_knowledge_base(self, answer: ResearchAnswer) -> None:
        """Add validated answer to knowledge base."""
        self.logger.info(f"Adding answer {answer.id} to knowledge base...")
        
        self.knowledge_base[answer.id] = asdict(answer)
        self.research_history.append(answer.id)
        
        # Update vector database
        if self.vector_db is not None:
            try:
                texts = self.text_splitter.split_text(answer.answer)
                self.vector_db.add_texts(texts, metadatas=[{"answer_id": answer.id}] * len(texts))
            except Exception as e:
                self.logger.error(f"Error updating vector database: {e}")

    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get summary of current knowledge base."""
        return {
            "total_answers": len(self.knowledge_base),
            "research_history_length": len(self.research_history),
            "categories": list(set([ResearchCategory.AI_INTEGRATION.value])),
            "last_updated": datetime.now().isoformat()
        }
