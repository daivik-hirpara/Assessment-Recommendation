# SHL Assessment Recommendation System
## Technical Approach Document

---

## 1. Problem Statement

Build an intelligent recommendation system that suggests relevant SHL assessments based on job descriptions or natural language queries.

**Requirements:**
- Handle cross-domain queries (technical + behavioral)
- Return 5-10 balanced recommendations with K/P/S type mix
- Achieve high Mean Recall@10 on evaluation dataset

---

## 2. Solution Architecture

```
User Query → FastAPI Server → Semantic Search (ChromaDB) → LLM Selection → Results
                                      ↓                           ↓
                            Sentence Transformers       Gemini 2.5 Flash
                                                        + Groq Llama 3.3
```

**Components:**

- **Data Pipeline**: Playwright + BeautifulSoup to scrape 389 assessments
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2) for semantic vectors
- **Vector Store**: ChromaDB with persistent storage for fast similarity search
- **LLM**: Gemini 2.5 Flash (primary) + Groq Llama 3.3 70B (fallback)
- **API**: FastAPI with /health and /recommend endpoints
- **Frontend**: HTML5, CSS3, Vanilla JavaScript

---

## 3. Data Pipeline

**Web Scraping Process:**
1. Navigated to SHL Product Catalog (type=1 for Individual Test Solutions)
2. Scraped 33 pages, extracting 389 unique assessments
3. Collected: Name, URL, Test Types (K/P/S), Remote/Adaptive support, Descriptions

**Data Quality Improvement:**
- Initial scrape: Only 12.9% had descriptions
- After optimization: 93.8% with descriptions (365/389)
- This significantly improved semantic search quality

---

## 4. Two-Stage Retrieval Approach

**Stage 1: Semantic Search**
- Index assessments with name + description + type keywords
- Use cosine similarity for retrieval
- Retrieve top 35 candidates for LLM selection pool

**Stage 2: LLM-Powered Selection**
- Pass candidates + query to Gemini/Groq with domain context
- LLM understands K (Knowledge), P (Personality), S (Simulation) types
- Selects best 10 with balanced type distribution
- Ensures cross-domain queries get mixed recommendations

---

## 5. Key Improvements Made

1. **Data Quality**: Scraped detailed descriptions for 93.8% of assessments
2. **Domain Context**: Added explicit K/P/S type explanations in LLM prompts
3. **Balanced Selection**: Instructed LLM to mix types for cross-domain queries
4. **Reliability**: Added Groq as fallback when Gemini fails

---

## 6. Challenges & Solutions

**Challenge 1: Low description coverage (12.9%)**
→ Solution: Re-scraped all 389 assessment detail pages

**Challenge 2: Semantic mismatch with ground truth**
→ Solution: Two-stage retrieval with LLM domain knowledge

**Challenge 3: LLM timeout errors**
→ Solution: Added Groq Llama 3.3 70B as fallback

**Challenge 4: Cross-domain query imbalance**
→ Solution: Explicit prompt instructions for K/P/S mix

---

## 7. API Specification

**Health Check Endpoint:**
```
GET /health
Response: {"status": "healthy", "assessments_indexed": 389}
```

**Recommendation Endpoint:**
```
POST /recommend
Request: {"query": "Java developer with collaboration skills", "max_results": 10}
Response: {"success": true, "recommendations": [...], "count": 10}
```

---

## 8. Technology Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector DB**: ChromaDB with persistent storage
- **LLM Primary**: Google Gemini 2.5 Flash
- **LLM Fallback**: Groq Llama 3.3 70B Versatile
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Scraping**: Playwright, BeautifulSoup, lxml
- **Deployment**: Render (Backend)
