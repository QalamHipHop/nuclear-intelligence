
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class ResearchQuestion(BaseModel):
    question: str = Field(description="The scientific question to be researched.")
    category: str = Field(description="The category of the question (e.g., Physics, Engineering, Economics, Safety).")
    difficulty: int = Field(description="Difficulty level of the question (1-10).")
    keywords: List[str] = Field(description="Key scientific terms related to the question.")

class ResearchAnswer(BaseModel):
    answer: str = Field(description="The detailed scientific answer with equations and analysis.")
    citations: List[str] = Field(description="List of scientific sources or academic references.")
    novelty_score: float = Field(description="Score (0-100) indicating the novelty of the insight.")
    accuracy_score: float = Field(description="Score (0-100) indicating scientific accuracy.")

class EvaluationScore(BaseModel):
    scientific_accuracy: float = Field(description="Scientific accuracy score (0-100).")
    novelty_score: float = Field(description="Novelty score (0-100).")
    usefulness_score: float = Field(description="Usefulness for the NES project (0-100).")
    self_consistency_check: bool = Field(description="Whether the answer is logically consistent.")
    justification: str = Field(description="Reasoning behind the evaluation scores.")

class KnowledgeGraph:
    def __init__(self, path: str = "knowledge_base/knowledge_graph.json"):
        self.path = path
        self.graph = {"entities": {}, "relationships": []}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    self.graph = json.load(f)
            except Exception as e:
                logger.error(f"Error loading Knowledge Graph: {e}")

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.graph, f, indent=4, ensure_ascii=False)

    def add_knowledge(self, question: str, answer: str, metadata: Dict[str, Any]):
        entity_id = hashlib.sha256(question.encode()).hexdigest()[:12]
        self.graph["entities"][entity_id] = {
            "question": question,
            "answer_summary": answer[:200] + "...",
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        # Simplified relationship: link to category
        category = metadata.get("category", "General")
        self.graph["relationships"].append({
            "from": entity_id,
            "to": category,
            "type": "belongs_to"
        })
        self._save()

class NuclearIntelligenceCore:
    def __init__(
        self,
        model_name: str = "gpt-4o",
        vector_db_path: str = "knowledge_base/faiss_index"
    ):
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        self.embeddings = OpenAIEmbeddings()
        self.vector_db_path = vector_db_path
        self.kg = KnowledgeGraph()
        self.vectorstore = self._init_vectorstore()

    def _init_vectorstore(self):
        if os.path.exists(self.vector_db_path):
            return FAISS.load_local(self.vector_db_path, self.embeddings, allow_dangerous_deserialization=True)
        else:
            # Initialize with a base document
            initial_text = "Nuclear Intelligence: Accelerating nuclear energy through AI and blockchain."
            vs = FAISS.from_texts([initial_text], self.embeddings)
            os.makedirs(os.path.dirname(self.vector_db_path), exist_ok=True)
            vs.save_local(self.vector_db_path)
            return vs

    def generate_question(self, context: str = "") -> ResearchQuestion:
        parser = PydanticOutputParser(pydantic_object=ResearchQuestion)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an advanced Nuclear Intelligence Architect. Generate a cutting-edge, complex research question that pushes the boundaries of nuclear science, fusion, or energy economics.\n{format_instructions}"),
            ("user", "Context: {context}\nGenerate a high-impact research question.")
        ])
        chain = prompt | self.llm | parser
        return chain.invoke({"context": context, "format_instructions": parser.get_format_instructions()})

    def conduct_research(self, question: ResearchQuestion) -> ResearchAnswer:
        # RAG: Retrieve context
        docs = self.vectorstore.similarity_search(question.question, k=3)
        context = "\n".join([d.page_content for d in docs])
        
        parser = PydanticOutputParser(pydantic_object=ResearchAnswer)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Senior Nuclear Scientist. Conduct deep research and provide a comprehensive, accurate answer with scientific rigor and citations.\n{format_instructions}"),
            ("user", "Question: {question}\nRelated Context: {context}\nProvide a detailed scientific answer.")
        ])
        chain = prompt | self.llm | parser
        return chain.invoke({
            "question": question.question, 
            "context": context, 
            "format_instructions": parser.get_format_instructions()
        })

    def evaluate_answer(self, question: ResearchQuestion, answer: ResearchAnswer) -> EvaluationScore:
        parser = PydanticOutputParser(pydantic_object=EvaluationScore)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an Independent Scientific Auditor. Evaluate the research output for accuracy, novelty, and project utility.\n{format_instructions}"),
            ("user", "Question: {question}\nAnswer: {answer}\nEvaluate this research output.")
        ])
        chain = prompt | self.llm | parser
        return chain.invoke({
            "question": question.question, 
            "answer": answer.answer, 
            "format_instructions": parser.get_format_instructions()
        })

    def integrate_knowledge(self, question: ResearchQuestion, answer: ResearchAnswer, evaluation: EvaluationScore):
        # Add to Vector Store
        content = f"Question: {question.question}\nAnswer: {answer.answer}"
        self.vectorstore.add_texts([content], metadatas=[{
            "category": question.category,
            "accuracy": evaluation.scientific_accuracy,
            "novelty": evaluation.novelty_score
        }])
        self.vectorstore.save_local(self.vector_db_path)
        
        # Add to Knowledge Graph
        self.kg.add_knowledge(question.question, answer.answer, {
            "category": question.category,
            "difficulty": question.difficulty,
            "accuracy": evaluation.scientific_accuracy
        })
        logger.info(f"Knowledge integrated for: {question.question[:50]}...")

import hashlib
