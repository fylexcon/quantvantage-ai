import logging
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import mean_absolute_error, mean_squared_error

from ml.data_loader import DEFAULT_WEIGHTS_DIR, StockDataLoader
from ml.model import HybridForecaster

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@dataclass
class AssetConfig:
    ticker: str
    asset_type: str
    period: str = "2y"
    batch_size: int = 16
    epochs: int = 50
    lr: float = 0.001
    patience: int = 5


class EarlyStopping:
    def __init__(self, patience=5):
        self.patience = patience
        self.counter = 0
        self.best_loss = float("inf")
        self.early_stop = False

    def __call__(self, val_loss):
        if val_loss < self.best_loss:
            self.best_loss = val_loss
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True


def train_and_evaluate_asset(
    config: AssetConfig, results_dir: Path, weights_dir: Path
) -> dict | None:
    safe_ticker = config.ticker.lower().replace("-", "_")
    logging.info("=" * 60)
    logging.info(f"STRESS TEST: {config.ticker} ({config.asset_type})")
    logging.info(
        f"Config -> Batch: {config.batch_size} | Epochs: {config.epochs} | LR: {config.lr}"
    )
    logging.info("=" * 60)

    scaler_path = weights_dir / f"{safe_ticker}_scaler.pkl"
    weights_path = weights_dir / f"{safe_ticker}_hybrid.pth"

    loader = StockDataLoader()

    try:
        bundle = loader.create_dataloaders(
            ticker=config.ticker,
            scaler_path=scaler_path,
            period=config.period,
            batch_size=config.batch_size,
        )
    except Exception as e:
        logging.error(f"Failed to fetch/create dataloaders for {config.ticker}: {e}")
        return None

    train_loader = bundle.train_loader
    val_loader = bundle.validation_loader

    model = HybridForecaster(
        input_size=len(bundle.feature_columns), forecast_horizon=7
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)
    criterion = nn.MSELoss()
    early_stopping = EarlyStopping(patience=config.patience)

    # --- Training Loop ---
    stopped_epoch = config.epochs
    for epoch in range(config.epochs):
        model.train()
        train_loss = 0.0
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            predictions = model(X_batch)
            loss = criterion(predictions, y_batch)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for X_val, y_val in val_loader:
                val_preds = model(X_val)
                v_loss = criterion(val_preds, y_val)
                val_loss += v_loss.item()

        avg_train_loss = train_loss / len(train_loader)
        avg_val_loss = val_loss / len(val_loader)

        if (epoch + 1) % 5 == 0 or epoch == 0:
            logging.info(
                f"Epoch {epoch+1:02d}/{config.epochs} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}"
            )

        early_stopping(avg_val_loss)
        if early_stopping.early_stop:
            logging.info(f"Early stopping triggered at Epoch {epoch+1}.")
            stopped_epoch = epoch + 1
            break

    # --- Save Asset Weights ---
    torch.save(model.state_dict(), weights_path)
    logging.info(f"Weights saved to {weights_path}")

    # --- Evaluation ---
    model.eval()
    actuals, predictions = [], []
    with torch.no_grad():
        for X_test, y_test in val_loader:
            preds = model(X_test)
            actuals.extend(y_test.numpy())
            predictions.extend(preds.numpy())

    actuals_dollars = loader.inverse_transform_target(
        np.array(actuals),
        scaler=bundle.scaler,
        target_column_index=bundle.target_column_index,
        feature_count=len(bundle.feature_columns),
    )
    predictions_dollars = loader.inverse_transform_target(
        np.array(predictions),
        scaler=bundle.scaler,
        target_column_index=bundle.target_column_index,
        feature_count=len(bundle.feature_columns),
    )

    mae = mean_absolute_error(actuals_dollars, predictions_dollars)
    rmse = np.sqrt(mean_squared_error(actuals_dollars, predictions_dollars))

    avg_price = float(np.mean(actuals_dollars))
    relative_error = (mae / avg_price) * 100

    # --- Plotting & Saving ---
    plt.figure(figsize=(10, 5))
    plt.plot(actuals_dollars, label=f"Actual {config.ticker} Price", color="blue", alpha=0.8)
    plt.plot(
        predictions_dollars,
        label=f"Predicted {config.ticker} Price",
        color="orange",
        linestyle="--",
        alpha=0.8,
    )
    plt.title(
        f"{config.ticker} 7-Day Forecast | MAE: ${mae:.2f} | Error: {relative_error:.2f}%"
    )
    plt.xlabel("Validation Window Step")
    plt.ylabel("Price (USD)")
    plt.legend()
    plt.grid(True)

    chart_path = results_dir / f"{safe_ticker}_forecast.png"
    plt.savefig(chart_path, bbox_inches="tight")
    plt.close()

    logging.info(f"Chart saved to {chart_path}\n")

    return {
        "Ticker": config.ticker,
        "Type": config.asset_type,
        "MAE ($)": f"${mae:.2f}",
        "RMSE ($)": f"${rmse:.2f}",
        "Avg Price": f"${avg_price:.2f}",
        "Error %": f"{relative_error:.2f}%",
        "Epochs": f"{stopped_epoch}/{config.epochs}",
    }


def main():
    base_dir = Path("ml")
    results_dir = base_dir / "results"
    weights_dir = base_dir / "weights"

    results_dir.mkdir(parents=True, exist_ok=True)
    weights_dir.mkdir(parents=True, exist_ok=True)

    roster = [
        AssetConfig(
            ticker="AAPL",
            asset_type="Equity (Baseline)",
            period="2y",
            batch_size=16,
            epochs=50,
            lr=1e-3,
        ),
        AssetConfig(
            ticker="IONQ",
            asset_type="High-Growth Tech",
            period="2y",
            batch_size=16,
            epochs=50,
            lr=1e-3,
        ),
        AssetConfig(
            ticker="BTC-USD",
            asset_type="Crypto (Major)",
            period="2y",
            batch_size=32,
            epochs=60,
            lr=5e-4,
        ),
        AssetConfig(
            ticker="ETH-USD",
            asset_type="Crypto (L1/DeFi)",
            period="2y",
            batch_size=32,
            epochs=60,
            lr=5e-4,
        ),
        AssetConfig(
            ticker="SOL-USD",
            asset_type="Crypto (High Vol)",
            period="2y",
            batch_size=32,
            epochs=60,
            lr=5e-4,
        ),
    ]

    summary = []
    for config in roster:
        res = train_and_evaluate_asset(config, results_dir, weights_dir)
        if res:
            summary.append(res)

    print("\n" + "=" * 88)
    print("MULTI-ASSET STRESS TEST COMPARATIVE SUMMARY")
    print("=" * 88)
    header = f"{'Ticker':<10} | {'Type':<20} | {'MAE ($)':<10} | {'RMSE ($)':<10} | {'Avg Price':<12} | {'Error %':<10} | {'Epochs':<8}"
    print(header)
    print("-" * len(header))
    for row in summary:
        print(
            f"{row['Ticker']:<10} | {row['Type']:<20} | {row['MAE ($)']:<10} | {row['RMSE ($)']:<10} | {row['Avg Price']:<12} | {row['Error %']:<10} | {row['Epochs']:<8}"
        )
    print("=" * 88 + "\n")


if __name__ == "__main__":
    main()
