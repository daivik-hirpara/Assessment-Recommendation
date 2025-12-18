"""
Assessment Recommendation Engine
Two-stage retrieval: semantic search + LLM selection with Groq fallback.
"""

import os
import re
import json
from typing import Optional
from pathlib import Path

import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv
import httpx

from embeddings import AssessmentVectorStore

load_dotenv()


class AssessmentRecommender:
    """RAG-based assessment recommendation engine with Groq fallback."""
    
    def __init__(self, vector_store: Optional[AssessmentVectorStore] = None):
        self.vector_store = vector_store or AssessmentVectorStore()
        
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini = genai.GenerativeModel("gemini-2.5-flash")
        else:
            self.gemini = None
        
        groq_key = os.getenv("GROQ_API_KEY")
        self.groq = Groq(api_key=groq_key) if groq_key else None
        
        if not self.gemini and not self.groq:
            raise ValueError("No LLM API key found (GEMINI_API_KEY or GROQ_API_KEY)")
    
    async def fetch_url_content(self, url: str) -> str:
        """Fetch text content from URL."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, follow_redirects=True)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "lxml")
                for el in soup(["script", "style", "nav", "footer"]):
                    el.decompose()
                text = soup.get_text(separator=" ", strip=True)
                return re.sub(r"\s+", " ", text)[:5000]
        except:
            return ""
    
    def _build_prompt(self, query: str, candidates: list[dict], max_results: int) -> str:
        """Build the selection prompt."""
        cand_text = "\n".join([
            f"{i+1}. {c['name']} [Types: {','.join(c.get('test_types',[]))}] - {c.get('description','')[:120]}"
            for i, c in enumerate(candidates[:35])
        ])
        
        return f"""You are an SHL assessment expert. Select the {max_results} BEST assessments for this job requirement.

ASSESSMENT TYPES (important for balanced recommendations):
- K (Knowledge/Skills): Tests technical abilities, aptitude, cognitive skills
- P (Personality/Behavior): OPQ, leadership, teamwork, communication traits
- S (Simulation): Practical hands-on tests, coding simulations

JOB REQUIREMENT:
{query[:2000]}

AVAILABLE ASSESSMENTS:
{cand_text}

SELECTION RULES:
1. Match assessments to the specific skills mentioned in the job
2. For technical roles: include relevant K-type skill tests
3. For roles needing soft skills: include P-type personality assessments
4. For cross-domain queries (both technical + soft skills): provide BALANCED mix of K and P types
5. Prefer assessments that match the seniority level (entry/mid/senior)
6. Include simulation tests (S) for hands-on practical roles

Return ONLY a JSON object: {{"selected": [1, 3, 5, ...]}}"""

    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API."""
        response = self.gemini.generate_content(prompt)
        return response.text.strip()
    
    def _call_groq(self, prompt: str) -> str:
        """Call Groq API."""
        completion = self.groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        return completion.choices[0].message.content.strip()
    
    def select_assessments(self, query: str, candidates: list[dict], max_results: int = 10) -> list[dict]:
        """Use LLM to select best assessments with fallback."""
        prompt = self._build_prompt(query, candidates, max_results)
        
        text = None
        
        if self.gemini:
            try:
                text = self._call_gemini(prompt)
            except Exception as e:
                print(f"Gemini error: {e}, trying Groq...")
        
        if not text and self.groq:
            try:
                text = self._call_groq(prompt)
            except Exception as e:
                print(f"Groq error: {e}")
        
        if not text:
            return candidates[:max_results]
        
        try:
            text = re.sub(r"^```json\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            result = json.loads(text)
            
            selected = []
            seen = set()
            for idx in result.get("selected", []):
                if 1 <= idx <= len(candidates):
                    a = candidates[idx - 1]
                    if a['url'] not in seen:
                        seen.add(a['url'])
                        selected.append(a)
            
            return selected[:max_results] if selected else candidates[:max_results]
        except Exception as e:
            print(f"Parse error: {e}")
            return candidates[:max_results]
    
    async def recommend(self, query: str, max_results: int = 10) -> list[dict]:
        """Get assessment recommendations for a query."""
        
        if query.startswith(("http://", "https://")):
            content = await self.fetch_url_content(query)
            if content:
                query = content
        
        candidates = self.vector_store.search(query, top_k=35)
        recommendations = self.select_assessments(query, candidates, max_results)
        
        for r in recommendations:
            r.pop("score", None)
        
        return recommendations
    
    def recommend_sync(self, query: str, max_results: int = 10) -> list[dict]:
        """Synchronous wrapper."""
        import asyncio
        return asyncio.run(self.recommend(query, max_results))


if __name__ == "__main__":
    rec = AssessmentRecommender()
    query = "Java developer with collaboration skills"
    print(f"Query: {query}\n")
    for i, r in enumerate(rec.recommend_sync(query), 1):
        print(f"{i}. {r['name']} ({r.get('test_types', [])})")
