"""
Embeddings and Vector Store Module
Creates searchable index of SHL assessments using ChromaDB.
"""

import json
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer


DATA_DIR = Path(__file__).parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"


class AssessmentVectorStore:
    """Vector store for SHL assessments."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
        
        self.collection = self.client.get_or_create_collection(
            name="shl_assessments",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        
        self._assessments_cache = None
    
    def load_assessments(self) -> list[dict]:
        """Load assessments from JSON file."""
        if self._assessments_cache is None:
            filepath = DATA_DIR / "assessments.json"
            with open(filepath, "r", encoding="utf-8") as f:
                self._assessments_cache = json.load(f)
        return self._assessments_cache
    
    def create_document_text(self, assessment: dict) -> str:
        """Create searchable text from assessment."""
        parts = [assessment.get('name', '')]
        
        desc = assessment.get('description', '')
        if desc:
            parts.append(desc)
        
        test_types = assessment.get("test_types", [])
        if "K" in test_types:
            parts.append("Knowledge Skills Technical Aptitude Test")
        if "P" in test_types:
            parts.append("Personality Behavioral Assessment OPQ")
        if "S" in test_types:
            parts.append("Simulation Practical Hands-on Test")
        
        return " | ".join(parts)
    
    def index_assessments(self, force_reindex: bool = False):
        """Index all assessments."""
        assessments = self.load_assessments()
        
        existing = self.collection.count()
        if existing > 0 and not force_reindex:
            print(f"Already indexed {existing} assessments")
            return
        
        if existing > 0:
            self.client.delete_collection("shl_assessments")
            self.collection = self.client.create_collection(
                name="shl_assessments",
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
        
        documents, metadatas, ids = [], [], []
        
        for i, a in enumerate(assessments):
            documents.append(self.create_document_text(a))
            metadatas.append({
                "name": a.get("name", ""),
                "url": a.get("url", ""),
                "test_types": ",".join(a.get("test_types", [])),
                "duration": a.get("duration", ""),
                "remote_support": a.get("remote_support", ""),
                "adaptive_support": a.get("adaptive_support", ""),
                "description": a.get("description", "")[:500]
            })
            ids.append(f"assessment_{i}")
        
        for i in range(0, len(documents), 100):
            end = min(i + 100, len(documents))
            self.collection.add(
                documents=documents[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end]
            )
        
        print(f"✅ Indexed {len(documents)} assessments")
    
    def search(self, query: str, top_k: int = 20) -> list[dict]:
        """Search for relevant assessments."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["metadatas", "distances"]
        )
        
        assessments = []
        if results["metadatas"] and results["metadatas"][0]:
            for i, meta in enumerate(results["metadatas"][0]):
                dist = results["distances"][0][i] if results["distances"] else 0
                types = meta.get("test_types", "")
                assessments.append({
                    "name": meta.get("name", ""),
                    "url": meta.get("url", ""),
                    "test_types": [t for t in types.split(",") if t],
                    "duration": meta.get("duration", ""),
                    "remote_support": meta.get("remote_support", ""),
                    "adaptive_support": meta.get("adaptive_support", ""),
                    "description": meta.get("description", ""),
                    "score": round(1 - dist, 3)
                })
        
        return assessments


if __name__ == "__main__":
    store = AssessmentVectorStore()
    store.index_assessments(force_reindex=True)
    
    print("\nTest search: 'Java developer'")
    for r in store.search("Java developer", top_k=5):
        print(f"  - {r['name']} ({r['score']})")
