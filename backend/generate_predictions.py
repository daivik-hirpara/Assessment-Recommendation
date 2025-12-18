"""
Generate predictions.csv for the test set.
"""

import requests
import pandas as pd
from pathlib import Path


API_URL = "http://localhost:8000"


TEST_QUERIES = [
    "I am hiring for Java developers who can also collaborate effectively with my business teams. Looking for an assessment(s) that can be completed in 40 minutes.",
    "Looking to hire mid-level professionals who are proficient in Python, SQL and JavaScript.",
    "I am hiring for an analyst and want applications to be screened using Cognitive and personality tests.",
    "We need customer service representatives who are good at problem-solving and can handle customer complaints efficiently.",
    "Looking for a comprehensive assessment package for graduate hiring in our technology division.",
    "Need to assess candidates for a senior marketing manager role with emphasis on strategic thinking and leadership.",
    "Hiring for a data scientist role requiring strong Python and machine learning skills.",
    "Looking for personality assessments for our management trainee program.",
    "Need technical assessments for full-stack developers with React and Node.js experience."
]


def main():
    print("Generating predictions for test set...\n")
    
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        print(f"API Status: {resp.json().get('status')}")
    except:
        print("❌ API not running! Start with: python main.py")
        return
    
    rows = []
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\nQuery {i}/{len(TEST_QUERIES)}: {query[:50]}...")
        
        try:
            resp = requests.post(
                f"{API_URL}/recommend",
                json={"query": query, "max_results": 10},
                timeout=120
            )
            recommendations = resp.json().get('recommendations', [])
            
            for rec in recommendations:
                rows.append({
                    "Query": query,
                    "Assessment_url": rec['url']
                })
            
            print(f"  Got {len(recommendations)} recommendations")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    df = pd.DataFrame(rows)
    output_file = Path(__file__).parent.parent / "predictions.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Saved {len(rows)} predictions to: {output_file}")
    print(f"   Queries: {len(TEST_QUERIES)}")
    print(f"   Avg recommendations per query: {len(rows)/len(TEST_QUERIES):.1f}")


if __name__ == "__main__":
    main()
