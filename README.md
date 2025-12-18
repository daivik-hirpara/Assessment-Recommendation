# SHL Assessment Recommendation System

An intelligent recommendation system that matches job descriptions and queries to relevant SHL assessments using AI.

## 🚀 Features

- **Natural Language Understanding**: Enter job descriptions or requirements in plain English
- **URL Support**: Paste job posting URLs to analyze
- **Balanced Recommendations**: Returns mix of Knowledge (K) and Personality (P) assessments
- **RAG Architecture**: Combines semantic search with LLM re-ranking

## 📋 Prerequisites

- Python 3.10+
- Google Gemini API key

## 🛠️ Setup

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
python -m playwright install chromium
```

2. **Set up environment:**
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_api_key_here
```

3. **Scrape assessment data** (optional - data included):
```bash
python scraper.py
```

4. **Initialize vector store:**
```bash
python embeddings.py
```

5. **Start the API server:**
```bash
python main.py
```

6. **Open the frontend:**
Open `frontend/index.html` in your browser.

## 📡 API Endpoints

### Health Check
```
GET /health
```

### Get Recommendations
```
POST /recommend
Content-Type: application/json

{
  "query": "Java developer with team collaboration skills",
  "max_results": 10
}
```

## 🏗️ Project Structure

```
shl-assign/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── scraper.py        # SHL catalog scraper
│   ├── embeddings.py     # Vector store setup
│   ├── recommender.py    # RAG recommendation engine
│   ├── evaluate.py       # Evaluation metrics
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── data/
│   └── assessments.json  # Scraped assessment data
└── docs/
    └── approach.md       # Technical approach document
```

## 📊 Evaluation

Run evaluation on training data:
```bash
python evaluate.py
```

Generate predictions for test set:
```bash
python generate_predictions.py
```

## 🔧 Technology Stack

- **Backend**: FastAPI, Python 3.12
- **Vector Store**: ChromaDB
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **LLM**: Google Gemini 2.5 Flash
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
