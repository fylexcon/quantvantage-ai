import sys
from fastapi.testclient import TestClient
from main import app
import uuid

try:
    client = TestClient(app)
except ImportError:
    print("httpx or requests not installed for TestClient. Skipping execution test.")
    sys.exit(0)

def run_tests():
    dedup = str(uuid.uuid4())
    print(f"Using dedup_hash: {dedup}")
    
    # 1. POST
    payload = {
        'ticker': 'NVDA',
        'score': 0.75,
        'sentiment_label': 'bullish',
        'article_count': 4,
        'dedup_hash': dedup
    }
    r1 = client.post('/api/sentiment', json=payload)
    print("POST /api/sentiment ->", r1.status_code, r1.json())
    
    # 2. GET limit
    r2 = client.get('/api/sentiment/NVDA?limit=5')
    print("GET /api/sentiment/NVDA ->", r2.status_code, r2.json())
    
    # 3. GET summary
    r3 = client.get('/api/sentiment/NVDA/summary')
    print("GET /api/sentiment/NVDA/summary ->", r3.status_code, r3.json())

if __name__ == "__main__":
    run_tests()
