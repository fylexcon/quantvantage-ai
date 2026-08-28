"""
train.py – Standalone training script for the SentimentImpactPredictor model.

Pulls historical sentiment records from Supabase via the batch dataset helpers,
wraps them in a PyTorch DataLoader, trains the model, and persists the updated
weights to disk.

Usage (from apps/api/):
    python train.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import torch
from torch import nn, optim
from torch.utils.data import DataLoader

# ---------------------------------------------------------------------------
# Path setup – ensure sibling packages are importable when running as a script
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

from ml.sentiment_model import SentimentImpactPredictor  # noqa: E402
from scripts.batch_sentiment_dataset import (  # noqa: E402
    SentimentHistoryDataset,
    fetch_historical_sentiment,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_DIM: int = 3
HIDDEN_DIM: int = 16
OUTPUT_DIM: int = 1         # SentimentImpactPredictor outputs a single score
BATCH_SIZE: int = 4
LEARNING_RATE: float = 1e-3
NUM_EPOCHS: int = 5
WEIGHTS_PATH: Path = _SCRIPT_DIR / "sentiment_model.pt"
TICKER: str = "AAPL"

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Training helpers
# ---------------------------------------------------------------------------

def _build_dataloader(ticker: str, batch_size: int) -> DataLoader:
    """Fetch historical sentiment rows for *ticker* and wrap in a DataLoader."""
    records = fetch_historical_sentiment(limit=10_000)
    # Filter to the requested ticker if a 'ticker' field exists in the rows
    filtered = [r for r in records if r.get("ticker", "").upper() == ticker.upper()]
    if not filtered:
        logger.warning(
            "No records matched ticker '%s'; falling back to all %d records.",
            ticker,
            len(records),
        )
        filtered = records

    dataset = SentimentHistoryDataset(filtered)
    logger.info("Dataset size: %d samples for ticker '%s'", len(dataset), ticker)

    return DataLoader(dataset, batch_size=batch_size, shuffle=True, drop_last=False)


def train(
    model: nn.Module,
    loader: DataLoader,
    *,
    epochs: int = NUM_EPOCHS,
    lr: float = LEARNING_RATE,
    device: torch.device | None = None,
) -> list[float]:
    """Standard MSE training loop with Adam optimiser.

    Returns the list of per-epoch average losses.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = model.to(device)
    model.train()

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    epoch_losses: list[float] = []

    for epoch in range(1, epochs + 1):
        running_loss = 0.0
        num_samples = 0

        for features, targets in loader:
            features = features.to(device)
            targets = targets.to(device)

            optimizer.zero_grad()
            predictions = model(features)
            loss = criterion(predictions, targets)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * features.size(0)
            num_samples += features.size(0)

        avg_loss = running_loss / max(num_samples, 1)
        epoch_losses.append(avg_loss)
        logger.info("Epoch %d/%d  –  Loss: %.6f", epoch, epochs, avg_loss)

    return epoch_losses


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    logger.info("=== SentimentImpactPredictor Training ===")
    logger.info(
        "Config: input_dim=%d, hidden_dim=%d, output_dim=%d, batch_size=%d, lr=%s, epochs=%d",
        INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM, BATCH_SIZE, LEARNING_RATE, NUM_EPOCHS,
    )

    # 1. Build DataLoader
    loader = _build_dataloader(ticker=TICKER, batch_size=BATCH_SIZE)

    if len(loader.dataset) == 0:  # type: ignore[arg-type]
        logger.error("No data available – aborting training.")
        sys.exit(1)

    # 2. Instantiate model
    model = SentimentImpactPredictor(
        input_features=INPUT_DIM,
        hidden_dim=HIDDEN_DIM,
    )
    logger.info("Model:\n%s", model)

    # 3. Train
    losses = train(model, loader, epochs=NUM_EPOCHS, lr=LEARNING_RATE)

    # 4. Save weights
    WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), WEIGHTS_PATH)
    logger.info("Model weights saved to %s", WEIGHTS_PATH)
    logger.info("Final training loss: %.6f", losses[-1])


if __name__ == "__main__":
    main()
