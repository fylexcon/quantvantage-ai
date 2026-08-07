from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

import torch
from torch import nn, optim
from torch.utils.data import DataLoader

from ml.data_loader import DEFAULT_WEIGHTS_DIR

logger = logging.getLogger(__name__)

DEFAULT_LEARNING_RATE: Final[float] = 1e-3
DEFAULT_WEIGHT_DECAY: Final[float] = 1e-5


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    validation_loader: DataLoader | None,
    *,
    epochs: int,
    learning_rate: float = DEFAULT_LEARNING_RATE,
    weight_decay: float = DEFAULT_WEIGHT_DECAY,
    device: torch.device | None = None,
) -> dict[str, list[float]]:
    """Trains the forecasting model using AdamW and MSE loss."""
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = model.to(device)
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    criterion = nn.MSELoss()
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=5)

    history: dict[str, list[float]] = {"train_loss": [], "val_loss": []}

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0

        for batch_features, batch_targets in train_loader:
            batch_features = batch_features.to(device)
            batch_targets = batch_targets.to(device)

            optimizer.zero_grad()
            predictions = model(batch_features)
            loss = criterion(predictions, batch_targets)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            train_loss += loss.item() * batch_features.size(0)

        epoch_train_loss = train_loss / len(train_loader.dataset)
        history["train_loss"].append(epoch_train_loss)

        if validation_loader is not None:
            model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for batch_features, batch_targets in validation_loader:
                    batch_features = batch_features.to(device)
                    batch_targets = batch_targets.to(device)
                    predictions = model(batch_features)
                    loss = criterion(predictions, batch_targets)
                    val_loss += loss.item() * batch_features.size(0)

            epoch_val_loss = val_loss / len(validation_loader.dataset)
            history["val_loss"].append(epoch_val_loss)
            scheduler.step(epoch_val_loss)

            logger.info(
                f"Epoch {epoch:03d}/{epochs} | Train Loss: {epoch_train_loss:.6f} | Val Loss: {epoch_val_loss:.6f}"
            )
        else:
            logger.info(f"Epoch {epoch:03d}/{epochs} | Train Loss: {epoch_train_loss:.6f}")

    return history


def save_model_weights(model: nn.Module, filename: str, *, weights_dir: Path = DEFAULT_WEIGHTS_DIR) -> Path:
    weights_dir.mkdir(parents=True, exist_ok=True)
    path = weights_dir / filename
    torch.save(model.state_dict(), path)
    return path


def load_model_weights(
    model: nn.Module, filename: str, *, weights_dir: Path = DEFAULT_WEIGHTS_DIR, device: torch.device | None = None
) -> nn.Module:
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    path = weights_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Model weights not found at {path}")
    model.load_state_dict(torch.load(path, map_location=device, weights_only=True))
    model.to(device)
    model.eval()
    return model


@torch.no_grad()
def predict(
    model: nn.Module,
    scaled_window: torch.Tensor,
    *,
    device: torch.device | None = None,
) -> torch.Tensor:
    """Runs inference on a pre-scaled historical window."""
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    model = model.to(device)
    model.eval()
    
    inputs = scaled_window.to(device)
    if inputs.ndim == 2:
        inputs = inputs.unsqueeze(0)
        
    predictions = model(inputs)
    return predictions.cpu()