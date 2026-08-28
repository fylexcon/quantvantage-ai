import logging
from typing import List, Tuple
import torch
from torch.utils.data import Dataset, DataLoader

# If run as a script directly from 'scripts' directory, ensure parent imports work
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import get_supabase_service_client

logger = logging.getLogger(__name__)

class SentimentHistoryDataset(Dataset):
    """
    A PyTorch Dataset that extracts features from historical sentiment records.
    It handles fallbacks between root-level fields and nested 'analysis' JSONB data.
    """
    def __init__(self, records: List[dict]):
        self.features = []
        self.targets = []  # Assuming model_prediction or some other label is the target for training
        
        for row in records:
            # Extract analysis object fallback
            analysis = row.get("analysis") or {}
            if not isinstance(analysis, dict):
                analysis = {}
                
            # Fallback logic: prefer root, fallback to nested JSONB analysis
            score = row.get("score")
            if score is None:
                score = analysis.get("score", 0.0)
                
            article_count = row.get("article_count")
            if article_count is None:
                article_count = analysis.get("article_count", 0)
                
            impact_weight = row.get("impact_weight")
            if impact_weight is None:
                impact_weight = analysis.get("impact_weight", 1.0)
                
            model_prediction = row.get("model_prediction", 0.0)
            if model_prediction is None:
                model_prediction = 0.0

            # Store the extracted features [score, impact_weight, article_count]
            feature_vector = [
                float(score), 
                float(impact_weight), 
                float(article_count)
            ]
            self.features.append(feature_vector)
            
            # Using model_prediction as target for self-supervised/distillation training proxy
            self.targets.append([float(model_prediction)])

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        x = torch.tensor(self.features[idx], dtype=torch.float32)
        y = torch.tensor(self.targets[idx], dtype=torch.float32)
        return x, y


def fetch_historical_sentiment(limit: int = 10000) -> List[dict]:
    """Fetches historical records from Supabase."""
    supabase = get_supabase_service_client()
    logger.info(f"Fetching up to {limit} records from sentiment_history...")
    
    # Using service_role client to bypass RLS and fetch bulk data
    result = (
        supabase.table("sentiment_history")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    records = result.data
    logger.info(f"Fetched {len(records)} records.")
    return records


def build_dataloader(batch_size: int = 32, limit: int = 10000) -> DataLoader:
    """Builds the PyTorch DataLoader containing historical sentiment data."""
    records = fetch_historical_sentiment(limit=limit)
    dataset = SentimentHistoryDataset(records)
    
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        drop_last=False
    )
    logger.info(f"Created DataLoader with {len(dataloader)} batches (batch_size={batch_size}).")
    return dataloader

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loader = build_dataloader(batch_size=4, limit=10)
    for batch_idx, (features, targets) in enumerate(loader):
        print(f"Batch {batch_idx}: Features Shape {features.shape}, Targets Shape {targets.shape}")
        print(features)
        break
