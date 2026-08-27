"""PyTorch prediction endpoints.

Loads pre-trained HybridForecaster weights once at startup, runs inference
on live OHLCV data fetched via yfinance, and returns multi-day price
forecasts with synthetic confidence intervals.
"""

from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np
import torch
from fastapi import APIRouter, BackgroundTasks, HTTPException

from database import get_supabase_service_client
from ml.data_loader import DEFAULT_WEIGHTS_DIR, StockDataLoader
from ml.engine import load_model_weights, predict
from ml.model import HybridForecaster
from models.schemas import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predict", tags=["Predictions"])

# ---------------------------------------------------------------------------
# Model registry — weights are loaded once per ticker and cached in-memory
# ---------------------------------------------------------------------------

_MODEL_CACHE: dict[str, tuple[HybridForecaster, str]] = {}
_CACHE_LOCK = Lock()

# The trained models all use 13 input features (5 OHLCV + 8 technical indicators)
# and a fixed 7-step forecast horizon.
_INPUT_SIZE = 13
_FORECAST_HORIZON = 7
_MODEL_VERSION = "hybrid-v1"


def _weight_filename(ticker: str) -> str:
    """Derive the on-disk weight filename for a ticker."""
    return f"{ticker.lower().replace('-', '_')}_hybrid.pth"


def _scaler_filename(ticker: str) -> str:
    """Derive the on-disk scaler filename for a ticker."""
    return f"{ticker.lower().replace('-', '_')}_scaler.pkl"


def _get_model(ticker: str) -> HybridForecaster:
    """Return a cached model for *ticker*, loading weights on first access."""
    normalized = ticker.strip().upper()
    if normalized in _MODEL_CACHE:
        return _MODEL_CACHE[normalized][0]

    with _CACHE_LOCK:
        # Double-check after acquiring the lock
        if normalized in _MODEL_CACHE:
            return _MODEL_CACHE[normalized][0]

        weights_file = _weight_filename(normalized)
        weights_path = DEFAULT_WEIGHTS_DIR / weights_file
        if not weights_path.exists():
            raise FileNotFoundError(
                f"No trained weights found for '{normalized}' at {weights_path}"
            )

        model = HybridForecaster(
            input_size=_INPUT_SIZE,
            forecast_horizon=_FORECAST_HORIZON,
        )
        load_model_weights(model, weights_file)
        _MODEL_CACHE[normalized] = (model, _MODEL_VERSION)
        logger.info("Loaded model weights for %s from %s", normalized, weights_path)
        return model


# ---------------------------------------------------------------------------
# Background persistence
# ---------------------------------------------------------------------------


def _persist_prediction(ticker: str, forecast_data: dict[str, Any]) -> None:
    """Persist a prediction payload to Supabase (fire-and-forget)."""
    try:
        supabase = get_supabase_service_client()
        supabase.table("predictions").insert(
            {"ticker": ticker, "forecast_data": forecast_data}
        ).execute()
        logger.info("Prediction persisted for %s", ticker)
    except Exception as exc:
        # Non-critical — log and move on; the client already has the result.
        logger.error("Failed to persist prediction for %s: %s", ticker, exc)


# ---------------------------------------------------------------------------
# POST /api/predict/{ticker}
# ---------------------------------------------------------------------------


@router.post("/{ticker}", response_model=PredictionResponse)
async def create_prediction(
    ticker: str,
    body: PredictionRequest,
    background_tasks: BackgroundTasks,
) -> PredictionResponse:
    """Run a multi-day price forecast for the given ticker.

    The request body may override ``days_ahead`` (1–30, default 7).
    The path *ticker* is canonical; ``body.ticker`` is ignored in favour of
    the path parameter.
    """
    normalized_ticker = ticker.strip().upper()
    days_ahead = body.days_ahead

    # ------------------------------------------------------------------
    # 1. Load or retrieve the cached model
    # ------------------------------------------------------------------
    try:
        model = _get_model(normalized_ticker)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Model loading failed for %s", normalized_ticker)
        raise HTTPException(
            status_code=500,
            detail=f"Model loading error: {exc}",
        ) from exc

    # ------------------------------------------------------------------
    # 2. Fetch the latest OHLCV window for inference
    # ------------------------------------------------------------------
    try:
        data_loader = StockDataLoader()
        scaler_path = DEFAULT_WEIGHTS_DIR / _scaler_filename(normalized_ticker)

        window_tensor, scaler = data_loader.load_latest_window(
            normalized_ticker,
            scaler_path=scaler_path,
        )
    except Exception as exc:
        logger.exception("Data fetch failed for %s", normalized_ticker)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch market data for '{normalized_ticker}': {exc}",
        ) from exc

    # ------------------------------------------------------------------
    # 3. Forward pass — handle days_ahead > forecast_horizon via rolling
    # ------------------------------------------------------------------
    try:
        feature_count = len(data_loader.feature_columns)
        target_idx = data_loader.target_column_index

        all_scaled_preds: list[float] = []
        current_window = window_tensor  # [1, lookback, features]

        remaining = days_ahead
        while remaining > 0:
            raw_pred = predict(model, current_window)  # [1, 7]
            pred_np = raw_pred.squeeze(0).numpy()
            take = min(_FORECAST_HORIZON, remaining)
            all_scaled_preds.extend(pred_np[:take].tolist())
            remaining -= take

            if remaining > 0:
                # Roll the window forward by appending predicted steps.
                # Build synthetic rows: copy last row's features and override
                # the target column with each predicted close.
                last_row = current_window[0, -1, :].numpy()  # [features]
                new_rows = []
                for step_val in pred_np[:take]:
                    row = last_row.copy()
                    row[target_idx] = step_val
                    new_rows.append(row)
                new_tensor = torch.from_numpy(
                    np.array(new_rows, dtype=np.float32)
                ).unsqueeze(0)
                # Slide window: drop oldest rows, append new ones
                current_window = torch.cat(
                    [current_window[:, take:, :], new_tensor], dim=1
                )

        # Inverse-transform scaled predictions back to dollar values
        forecasted_prices_raw = StockDataLoader.inverse_transform_target(
            all_scaled_preds,
            scaler=scaler,
            target_column_index=target_idx,
            feature_count=feature_count,
        )
        forecasted_prices = [round(float(p), 2) for p in forecasted_prices_raw]

    except Exception as exc:
        logger.exception("Inference failed for %s", normalized_ticker)
        raise HTTPException(
            status_code=500,
            detail=f"Model inference error: {exc}",
        ) from exc

    # ------------------------------------------------------------------
    # 4. Current price — last raw close from the fetched history
    # ------------------------------------------------------------------
    try:
        history = data_loader.fetch_history(normalized_ticker, period="5d")
        current_price = round(float(history["Close"].iloc[-1]), 2)
    except Exception:
        # Fallback: treat the first forecasted price as a proxy
        current_price = forecasted_prices[0] if forecasted_prices else 0.0

    # ------------------------------------------------------------------
    # 5. Synthetic confidence intervals (±1σ / ±2σ bands)
    # ------------------------------------------------------------------
    prices_arr = np.array(forecasted_prices, dtype=np.float64)
    base_std = np.std(prices_arr) if len(prices_arr) > 1 else prices_arr[0] * 0.02
    # Widen the band linearly over the forecast horizon
    horizon_factors = np.linspace(0.5, 1.5, len(prices_arr))
    sigma_1 = base_std * horizon_factors
    sigma_2 = 2.0 * sigma_1

    confidence_intervals: dict[str, list[float]] = {
        "upper_1σ": [round(float(p + s), 2) for p, s in zip(prices_arr, sigma_1)],
        "lower_1σ": [round(float(p - s), 2) for p, s in zip(prices_arr, sigma_1)],
        "upper_2σ": [round(float(p + s), 2) for p, s in zip(prices_arr, sigma_2)],
        "lower_2σ": [round(float(p - s), 2) for p, s in zip(prices_arr, sigma_2)],
    }

    # ------------------------------------------------------------------
    # 6. Queue background persistence to Supabase
    # ------------------------------------------------------------------
    forecast_payload: dict[str, Any] = {
        "days_ahead": days_ahead,
        "forecasted_prices": forecasted_prices,
        "confidence_intervals": confidence_intervals,
        "current_price": current_price,
        "model_version": _MODEL_VERSION,
    }
    background_tasks.add_task(_persist_prediction, normalized_ticker, forecast_payload)

    # ------------------------------------------------------------------
    # 7. Return validated response
    # ------------------------------------------------------------------
    return PredictionResponse(
        ticker=normalized_ticker,
        current_price=current_price,
        forecasted_prices=forecasted_prices,
        confidence_intervals=confidence_intervals,
        model_version=_MODEL_VERSION,
    )
