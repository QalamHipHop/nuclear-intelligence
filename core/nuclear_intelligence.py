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
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
import requests
import arxiv
from .. import default_api # Import the default_api for search tool


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
            self.logger.debug(f"Added node: {node_id} with properties {properties}")
        else:
            self.nodes[node_id].update(properties)
            self.logger.debug(f"Updated node: {node_id} with properties {properties}")

    def add_edge(self, source_id: str, target_id: str, relationship_type: str, properties: Optional[Dict[str, Any]] = None):
        if source_id not in self.nodes:
            self.logger.warning(f"Source node {source_id} not found. Cannot add edge.")
            return
        if target_id not in self.nodes:
            self.logger.warning(f"Target node {target_id} not found. Cannot add edge.")
            return
        
        edge = {
            "target": target_id,
            "type": relationship_type,
            "properties": properties if properties is not None else {}
        }
        self.edges[source_id].append(edge)
        self.logger.debug(f"Added edge from {source_id} to {target_id} of type {relationship_type}")

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        return self.nodes.get(node_id)

    def get_edges(self, node_id: str) -> List[Dict[str, Any]]:
        return self.edges.get(node_id, [])

    def add_answer_to_graph(self, answer: ResearchAnswer):
        """Extract entities and relationships from a ResearchAnswer and add to graph."""
        self.logger.info(f"Adding answer {answer.id} to knowledge graph...")
        
        # Add the answer itself as a node
        answer_node_id = f"answer_{answer.id}"
        self.add_node(answer_node_id, {
            "type": "ResearchAnswer",
            "question_id": answer.question_id,
            "summary": answer.answer[:200] + "...",
            "timestamp": answer.timestamp.isoformat(),
            "model_version": answer.model_version,
            "scientific_accuracy": answer.evaluation_scores.scientific_accuracy
        })
        
        # Add the question as a node and link it
        question_node_id = f"question_{answer.question_id}"
        self.add_node(question_node_id, {
            "type": "ResearchQuestion",
            "question_text": answer.question_id, # This should be the actual question text, not ID
            "timestamp": answer.timestamp.isoformat()
        })
        self.add_edge(question_node_id, answer_node_id, "HAS_ANSWER")
        self.add_edge(answer_node_id, question_node_id, "ANSWERS")

        # Extract entities from the answer text and link them
        # This is a simplified entity extraction. A more advanced version would use NLP.
        entities = self._extract_entities_from_text(answer.answer)
        for entity_name, entity_type in entities:
            entity_id = f"entity_{hashlib.md5(entity_name.encode()).hexdigest()[:8]}"
            self.add_node(entity_id, {"type": entity_type, "name": entity_name})
            self.add_edge(answer_node_id, entity_id, "MENTIONS")
            self.add_edge(entity_id, answer_node_id, "MENTIONED_IN")

        # Link sources
        for source in answer.sources:
            source_id = f"source_{hashlib.md5(source['url'].encode()).hexdigest()[:8]}"
            self.add_node(source_id, {"type": source['type'], "title": source['title'], "url": source['url']})
            self.add_edge(answer_node_id, source_id, "CITED_FROM")
            self.add_edge(source_id, answer_node_id, "CITES")

    def _extract_entities_from_text(self, text: str) -> List[Tuple[str, str]]:
        """A placeholder for entity extraction from text."""
        # In a real system, this would use NER (Named Entity Recognition)
        # For now, we can look for some keywords or use a simple regex.
        entities = []
        # Example: look for capitalized words that are not at the beginning of a sentence
        import re
        potential_entities = re.findall(r'\b[A-Z][a-z0-9]+(?:\s[A-Z][a-z0-9]+)*\b', text)
        for pe in potential_entities:
            if len(pe.split()) > 1 or pe.lower() not in ["the", "a", "an", "and", "or", "but", "for", "nor", "so", "yet", "in", "on", "at", "by", "with", "from", "of", "to", "is", "are", "was", "were", "be", "been", "being"]:
                entities.append((pe, "Concept"))
        return list(set(entities)) # Return unique entities

    def to_json(self) -> Dict[str, Any]:
        """Serialize the knowledge graph to a JSON-compatible dictionary."""
        return {
            "nodes": self.nodes,
            "edges": {k: list(v) for k, v in self.edges.items()}
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]):
        """Deserialize the knowledge graph from a JSON-compatible dictionary."""
        graph = cls()
        graph.nodes = data.get("nodes", {})
        graph.edges = defaultdict(list, {k: v for k, v in data.get("edges", {}).items()})
        return graph

    def get_node_count(self) -> int:
        return len(self.nodes)

    def get_edge_count(self) -> int:
        return sum(len(v) for v in self.edges.values())


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
        self.knowledge_graph = KnowledgeGraph()
        
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
        try:
            search_results = default_api.search(brief="Perform web search for current information.", type="info", queries=[query])
            web_results = []
            for result in search_results.get("results", []):
                web_results.append({"title": result.get("title"), "url": result.get("url"), "snippet": result.get("snippet")})
            return web_results
        except Exception as e:
            self.logger.error(f"Error performing web search: {e}")
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
        
        context += "\n## Web Search Results\n"
        for result in web_results[:3]:
            context += f"- **{result['title']}** ({result['url']})\n"
            context += f"  {result['snippet'][:200]}...\n"
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
        for result in web_results:
            sources.append({
                "type": "web",
                "title": result["title"],
                "url": result["url"],
                "snippet": result["snippet"]
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
        
        # Add answer content to knowledge graph
        self.knowledge_graph.add_answer_to_graph(answer)
        
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
            "last_updated": datetime.now().isoformat(),
            "knowledge_graph_nodes": self.knowledge_graph.get_node_count(),
            "knowledge_graph_edges": self.knowledge_graph.get_edge_count()
        }
