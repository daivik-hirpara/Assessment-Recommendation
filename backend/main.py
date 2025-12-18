"""
SHL Assessment Recommendation API
FastAPI application with /health and /recommend endpoints.
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from embeddings import AssessmentVectorStore
from recommender import AssessmentRecommender


load_dotenv()


vector_store: Optional[AssessmentVectorStore] = None
recommender: Optional[AssessmentRecommender] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize components on startup."""
    global vector_store, recommender
    
    print("🚀 Starting SHL Assessment Recommendation System...")
    
    vector_store = AssessmentVectorStore()
    vector_store.index_assessments()
    
    recommender = AssessmentRecommender(vector_store)
    print("✅ System ready")
    
    yield
    
    print("👋 Shutting down")


app = FastAPI(
    title="SHL Assessment Recommendation API",
    description="Recommends relevant SHL assessments for job descriptions",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10


class Assessment(BaseModel):
    name: str
    url: str
    test_types: list[str] = []
    duration: str = ""
    remote_support: str = ""
    adaptive_support: str = ""
    description: str = ""


class RecommendResponse(BaseModel):
    success: bool
    recommendations: list[Assessment]
    count: int


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model": "gemini-2.5-flash",
        "assessments_indexed": vector_store.collection.count() if vector_store else 0
    }


@app.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    """Get assessment recommendations for a query."""
    if not recommender:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if not request.query or len(request.query.strip()) < 5:
        raise HTTPException(status_code=400, detail="Query too short")
    
    max_results = min(max(request.max_results or 10, 1), 10)
    
    try:
        results = await recommender.recommend(request.query, max_results)
        
        return RecommendResponse(
            success=True,
            recommendations=[Assessment(**r) for r in results],
            count=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

