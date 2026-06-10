"""Nuclear Intelligence - Embedding Engine - Local & FREE"""
import os
from typing import List, Optional
from loguru import logger

class EmbeddingEngine:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or "sentence-transformers/all-MiniLM-L6-v2"
        self._model = None
        self._embedding_dim = 384

    @property
    def model(self):
        if self._model is None:
            logger.info(f"Loading: {self.model_name}")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            self._embedding_dim = self._model.get_sentence_embedding_dimension()
            logger.info(f"✅ Embedding model loaded. Dim: {self._embedding_dim}")
        return self._model

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_single(self, text: str) -> List[float]:
        return self.embed([text])[0]

    def load_or_create_vectordb(self, path: str, initial_text: Optional[str] = None):
        try:
            from langchain_community.vectorstores import FAISS
            from langchain_huggingface import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
            if os.path.exists(path):
                try: return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
                except: pass
            texts = [initial_text] if initial_text else ["Nuclear Intelligence: AI-powered nuclear research."]
            vs = FAISS.from_texts(texts, embeddings)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            vs.save_local(path)
            logger.info(f"Created new FAISS index at {path}")
            return vs
        except Exception as e:
            logger.error(f"Vector store error: {e}")
            return None

    def get_stats(self) -> dict:
        return {"model": self.model_name, "dimension": self._embedding_dim, "type": "local (no API cost)"}
