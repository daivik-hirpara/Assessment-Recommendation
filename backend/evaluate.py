"""
Evaluation script for Mean Recall@10.
Tests the recommendation system against labeled training data.
"""

import requests
import pandas as pd
from pathlib import Path


API_URL = "http://localhost:8000"
TRAIN_FILE = Path(__file__).parent.parent / "Gen_AI Dataset.xlsx"


def extract_slug(url: str) -> str:
    """Extract assessment slug from URL for comparison."""
    url = str(url).lower()
    if 'view/' in url:
        return url.split('view/')[-1].rstrip('/')
    return url


def main():
    print("=" * 60)
    print("SHL ASSESSMENT RECOMMENDER - EVALUATION")
    print("=" * 60)
    
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        print(f"\nAPI Status: {resp.json().get('status', 'unknown')}")
    except:
        print("\n❌ API not running! Start with: python main.py")
        return
    
    print("\nLoading training data...")
    df = pd.read_excel(TRAIN_FILE)
    print(f"Total rows: {len(df)}")
    
    grouped = df.groupby('Query')['Assessment_url'].apply(list).to_dict()
    print(f"Unique queries: {len(grouped)}")
    
    print("\n" + "-" * 60)
    print("EVALUATING...")
    print("-" * 60)
    
    total_recall = 0
    query_results = []
    
    for query, gt_urls in grouped.items():
        gt_slugs = set(extract_slug(u) for u in gt_urls)
        
        try:
            resp = requests.post(
                f"{API_URL}/recommend",
                json={"query": query, "max_results": 10},
                timeout=120
            )
            predictions = resp.json().get('recommendations', [])
            pred_slugs = set(extract_slug(p['url']) for p in predictions)
        except Exception as e:
            print(f"\n❌ Error on query: {str(e)[:50]}")
            pred_slugs = set()
        
        matches = gt_slugs & pred_slugs
        recall = len(matches) / len(gt_slugs) if gt_slugs else 0
        total_recall += recall
        
        query_results.append({
            'query': query[:50] + "...",
            'gt_count': len(gt_slugs),
            'pred_count': len(pred_slugs),
            'matches': len(matches),
            'recall': recall
        })
        
        print(f"\nQuery: {query[:60]}...")
        print(f"  Ground truth: {len(gt_slugs)}, Predicted: {len(pred_slugs)}, Matches: {len(matches)}")
        print(f"  Recall@10: {recall*100:.1f}%")
        if matches:
            print(f"  Matched: {list(matches)[:3]}...")
    
    mean_recall = total_recall / len(grouped) if grouped else 0
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"\nQueries evaluated: {len(grouped)}")
    print(f"Total matches: {sum(r['matches'] for r in query_results)}/{sum(r['gt_count'] for r in query_results)}")
    print(f"\n{'='*40}")
    print(f"  MEAN RECALL@10: {mean_recall*100:.1f}%")
    print(f"{'='*40}")


if __name__ == "__main__":
    main()
