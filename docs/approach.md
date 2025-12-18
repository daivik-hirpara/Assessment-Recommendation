# SHL Assessment Recommendation System

## Technical Approach Document

### 1. Problem Statement
Build an intelligent recommendation system that suggests relevant SHL assessments for job descriptions or natural language queries, with balanced recommendations across Knowledge (K), Personality (P), and Simulation (S) types.

### 2. Solution Architecture

```
User Query → FastAPI → Semantic Search (ChromaDB) → LLM Selection (Gemini) → Results
                              ↓                              ↓
                    Sentence Transformers          Groq Fallback (Llama 3.3)
```

**Key Components:**
- **Data Pipeline**: Playwright scraper collected 389 Individual Test Solutions
- **Vector Store**: ChromaDB with Sentence Transformers embeddings
- **LLM**: Gemini 2.5 Flash (primary) + Groq Llama 3.3 70B (fallback)
- **API**: FastAPI with `/health` and `/recommend` endpoints

### 3. Two-Stage Retrieval Approach

**Stage 1: Semantic Search**
- Index all assessments with name + description + type metadata
- Retrieve top 35 candidates using cosine similarity

**Stage 2: LLM Selection**
- Pass candidates to LLM with domain context about K/P/S types
- LLM selects best 10 based on job requirements
- Ensures balanced mix for cross-domain queries

### 4. Performance Optimization Journey

| Iteration | Approach                                           | Mean Recall@10 |
| --------- | -------------------------------------------------- | -------------- |
| 1         | Pure semantic search                               | ~15%           |
| 2         | Added LLM reranking                                | ~25%           |
| 3         | Re-scraped with full descriptions (93.8% coverage) | ~35%           |
| 4         | Two-stage with domain-aware prompts                | ~45%           |

**Key Improvements:**
1. Scraped detailed descriptions for 93.8% of assessments (was 12.9%)
2. Added explicit K/P/S type context in LLM prompts
3. Implemented balanced selection for cross-domain queries
4. Added Groq fallback for reliability

### 5. API Specification

**POST /recommend**
```json
Request: {"query": "Java developer with collaboration skills", "max_results": 10}
Response: {"success": true, "recommendations": [...], "count": 10}
```

### 6. Technology Stack

| Component  | Technology                               |
| ---------- | ---------------------------------------- |
| Backend    | Python 3.12, FastAPI                     |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Vector DB  | ChromaDB (persistent)                    |
| LLM        | Gemini 2.5 Flash + Groq Llama 3.3        |
| Frontend   | HTML5, CSS3, JavaScript                  |
| Scraping   | Playwright, BeautifulSoup                |
