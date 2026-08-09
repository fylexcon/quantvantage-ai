from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence, cast

import joblib
import numpy as np
import pandas as pd
import torch
import yfinance as yf
from numpy.typing import NDArray
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, Dataset, random_split

DEFAULT_FEATURE_COLUMNS: Final[tuple[str, ...]] = ("Open", "High", "Low", "Close", "Volume")
DEFAULT_TARGET_COLUMN: Final[str] = "Close"
DEFAULT_LOOKBACK_DAYS: Final[int] = 60
DEFAULT_FORECAST_HORIZON: Final[int] = 7
DEFAULT_BATCH_SIZE: Final[int] = 32
DEFAULT_WEIGHTS_DIR: Final[Path] = Path(__file__).resolve().parent / "weights"

FloatArray = NDArray[np.float32]


@dataclass(frozen=True, slots=True)
class DataLoaderBundle:
    train_loader: DataLoader
    validation_loader: DataLoader | None
    scaler: MinMaxScaler
    feature_columns: tuple[str, ...]
    target_column_index: int
    dataset: "StockWindowDataset"


class StockWindowDataset(Dataset):
    """Sliding-window dataset for supervised multi-step stock forecasting."""

    def __init__(
        self,
        scaled_values: FloatArray,
        *,
        target_column_index: int,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        forecast_horizon: int = DEFAULT_FORECAST_HORIZON,
    ) -> None:
        if scaled_values.ndim != 2:
            raise ValueError("scaled_values must be a 2D array shaped as [time, features].")
        if lookback_days < 1:
            raise ValueError("lookback_days must be greater than zero.")
        if forecast_horizon < 1:
            raise ValueError("forecast_horizon must be greater than zero.")
        if target_column_index < 0 or target_column_index >= scaled_values.shape[1]:
            raise ValueError("target_column_index is outside the available feature range.")
        minimum_rows = lookback_days + forecast_horizon
        if scaled_values.shape[0] < minimum_rows:
            raise ValueError(
                f"At least {minimum_rows} rows are required to build forecasting windows."
            )

        self._values = scaled_values.astype(np.float32, copy=False)
        self._target_column_index = target_column_index
        self._lookback_days = lookback_days
        self._forecast_horizon = forecast_horizon
        self._window_count = scaled_values.shape[0] - lookback_days - forecast_horizon + 1

    def __len__(self) -> int:
        return self._window_count

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        if index < 0 or index >= self._window_count:
            raise IndexError("StockWindowDataset index out of range.")

        lookback_end = index + self._lookback_days
        forecast_end = lookback_end + self._forecast_horizon
        features = self._values[index:lookback_end]
        targets = self._values[lookback_end:forecast_end, self._target_column_index]

        return torch.from_numpy(features), torch.from_numpy(targets)


class StockDataLoader:
    """Fetches OHLCV data, scales it, and builds PyTorch training loaders."""

    def __init__(
        self,
        *,
        feature_columns: Sequence[str] = DEFAULT_FEATURE_COLUMNS,
        target_column: str = DEFAULT_TARGET_COLUMN,
    ) -> None:
        if target_column not in feature_columns:
            raise ValueError("target_column must be present in feature_columns.")

        self.feature_columns = tuple(feature_columns)
        self.target_column = target_column
        self.target_column_index = self.feature_columns.index(target_column)

    def fetch_history(
        self,
        ticker: str,
        *,
        period: str = "5y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        symbol = self._normalize_ticker(ticker)
        frame = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
            group_by="column",
        )
        if frame.empty:
            raise ValueError(f"No historical data returned for ticker '{symbol}'.")

        normalized = self._normalize_yfinance_frame(frame, symbol)
        missing_columns = [column for column in self.feature_columns if column not in normalized.columns]
        if missing_columns:
            raise ValueError(f"Missing required OHLCV columns for {symbol}: {missing_columns}")

        cleaned = normalized.loc[:, self.feature_columns].copy()
        cleaned = cleaned.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
        cleaned = cleaned.dropna().sort_index()
        if cleaned.empty:
            raise ValueError(f"Historical data for '{symbol}' contains no usable OHLCV rows.")

        return cleaned

    def fit_transform(
        self,
        frame: pd.DataFrame,
        *,
        scaler_path: str | Path | None = None,
    ) -> tuple[FloatArray, MinMaxScaler]:
        values = self._frame_to_feature_array(frame)
        scaler = MinMaxScaler()
        scaled = cast(FloatArray, scaler.fit_transform(values).astype(np.float32))

        if scaler_path is not None:
            self.save_scaler(scaler, scaler_path)

        return scaled, scaler

    def transform(self, frame: pd.DataFrame, scaler: MinMaxScaler) -> FloatArray:
        values = self._frame_to_feature_array(frame)
        return cast(FloatArray, scaler.transform(values).astype(np.float32))

    def create_dataset(
        self,
        scaled_values: FloatArray,
        *,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        forecast_horizon: int = DEFAULT_FORECAST_HORIZON,
    ) -> StockWindowDataset:
        return StockWindowDataset(
            scaled_values,
            target_column_index=self.target_column_index,
            lookback_days=lookback_days,
            forecast_horizon=forecast_horizon,
        )

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Injects momentum, trend, and volatility indicators into the raw price data."""

        # 1. RSI (Relative Strength Index) - 14 Day Window
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()

        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 2. MACD (Moving Average Convergence Divergence)
        ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema_12 - ema_26

        # MACD Signal Line (9-day EMA of the MACD)
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # ---------------------------------------------------------
        # NEW: VOLATILITY INDICATORS (Bollinger Bands & ATR)
        # ---------------------------------------------------------

        # 3. Bollinger Bands (20-day SMA & 2 Standard Deviations)
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)

        # Optional but highly recommended: Bollinger Bandwidth
        # This gives the model a single number to measure how "squeezed" the price is
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']

        # 4. ATR (Average True Range) - 14-day
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()

        # True Range is the maximum of the three values above
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(window=14).mean()

        # ---------------------------------------------------------

        # Clean up the NaN values created by rolling windows
        df.fillna(0, inplace=True)

        return df

    def create_dataloaders(
        self,
        ticker: str,
        *,
        scaler_path: str | Path,
        period: str = "5y",
        interval: str = "1d",
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        forecast_horizon: int = DEFAULT_FORECAST_HORIZON,
        batch_size: int = DEFAULT_BATCH_SIZE,
        validation_split: float = 0.2,
        shuffle_train: bool = True,
    ) -> DataLoaderBundle:
        if batch_size < 1:
            raise ValueError("batch_size must be greater than zero.")
        if validation_split < 0.0 or validation_split >= 1.0:
            raise ValueError("validation_split must be in the range [0.0, 1.0).")

        # Step 1: Fetch data using yfinance
        history = self.fetch_history(ticker, period=period, interval=interval)

        # Step 2: Add Technical Indicators to the raw data
        history_with_indicators = self.add_technical_indicators(history)
        self.feature_columns = tuple(history_with_indicators.columns)

        # Step 3: Fit the scaler and transform the data
        scaled_values, scaler = self.fit_transform(history_with_indicators, scaler_path=scaler_path)

        # Step 4: Create the sliding-window dataset
        dataset = self.create_dataset(
            scaled_values,
            lookback_days=lookback_days,
            forecast_horizon=forecast_horizon,
        )

        # Step 5: Split into Train / Validation
        train_size = int((1.0 - validation_split) * len(dataset))
        train_dataset, test_dataset = random_split(dataset, [train_size, len(dataset) - train_size])

        # Step 6: Create the DataLoaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=shuffle_train,
        )
        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,  # Always False for validation/testing
        )

        return DataLoaderBundle(
            train_loader=train_loader,
            validation_loader=test_loader,
            scaler=scaler,
            feature_columns=self.feature_columns,
            target_column_index=self.target_column_index,
            dataset=dataset,
        )

    def load_latest_window(
        self,
        ticker: str,
        *,
        scaler_path: str | Path,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        period: str = "6mo",
        interval: str = "1d",
    ) -> tuple[torch.Tensor, MinMaxScaler]:
        scaler = self.load_scaler(scaler_path)
        history = self.fetch_history(ticker, period=period, interval=interval)
        history_with_indicators = self.add_technical_indicators(history)
        self.feature_columns = tuple(history_with_indicators.columns)
        if len(history_with_indicators) < lookback_days:
            raise ValueError(
                f"Need at least {lookback_days} usable rows for inference, got {len(history_with_indicators)}."
            )

        latest_values = history_with_indicators.tail(lookback_days)
        scaled_latest = self.transform(latest_values, scaler)
        return torch.from_numpy(scaled_latest).unsqueeze(0), scaler

    def save_scaler(self, scaler: MinMaxScaler, path: str | Path) -> Path:
        """Save the fitted scaler to a file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(scaler, path)
        return path

    def load_scaler(self, path: str | Path) -> MinMaxScaler:
        """Load a fitted scaler from a file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Scaler file does not exist: {path}")
        scaler = joblib.load(path)
        if not isinstance(scaler, MinMaxScaler):
            raise TypeError(f"Expected a MinMaxScaler at {path}, got {type(scaler)!r}.")
        return scaler

    @staticmethod
    def inverse_transform_target(
        scaled_values: Sequence[float] | NDArray[np.float32] | NDArray[np.float64],
        *,
        scaler: MinMaxScaler,
        target_column_index: int,
        feature_count: int,
    ) -> FloatArray:
        scaled_array = np.asarray(scaled_values, dtype=np.float32).reshape(-1)
        feature_template = np.zeros((scaled_array.shape[0], feature_count), dtype=np.float32)
        feature_template[:, target_column_index] = scaled_array
        unscaled = scaler.inverse_transform(feature_template)
        return cast(FloatArray, unscaled[:, target_column_index].astype(np.float32))

    def _frame_to_feature_array(self, frame: pd.DataFrame) -> FloatArray:
        missing_columns = [column for column in self.feature_columns if column not in frame.columns]
        if missing_columns:
            raise ValueError(f"Missing required feature columns: {missing_columns}")

        values = frame.loc[:, self.feature_columns].to_numpy(dtype=np.float32)
        if values.ndim != 2 or values.shape[0] == 0:
            raise ValueError("Feature frame must contain at least one row.")
        return cast(FloatArray, values)

    @staticmethod
    def _normalize_ticker(ticker: str) -> str:
        symbol = ticker.strip().upper()
        if not symbol:
            raise ValueError("ticker must not be empty.")
        return symbol

    @staticmethod
    def _normalize_yfinance_frame(frame: pd.DataFrame, ticker: str) -> pd.DataFrame:
        normalized = frame.copy()
        if isinstance(normalized.columns, pd.MultiIndex):
            last_level_values = set(map(str, normalized.columns.get_level_values(-1)))
            first_level_values = set(map(str, normalized.columns.get_level_values(0)))
            if ticker in last_level_values:
                normalized = normalized.xs(ticker, axis=1, level=-1, drop_level=True)
            elif ticker in first_level_values:
                normalized = normalized.xs(ticker, axis=1, level=0, drop_level=True)
            else:
                normalized.columns = normalized.columns.get_level_values(0)

        rename_map = {column: str(column).strip().title() for column in normalized.columns}
        return normalized.rename(columns=rename_map)