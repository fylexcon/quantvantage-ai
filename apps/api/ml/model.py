from __future__ import annotations

import math

import torch
from torch import nn


class PositionalEncoding(nn.Module):
    """Sinusoidal position encoding for order-aware Transformer processing."""

    def __init__(self, model_dim: int, *, dropout: float = 0.1, max_length: int = 512) -> None:
        super().__init__()
        if model_dim < 1:
            raise ValueError("model_dim must be greater than zero.")
        if max_length < 1:
            raise ValueError("max_length must be greater than zero.")

        self.dropout = nn.Dropout(p=dropout)

        positions = torch.arange(max_length, dtype=torch.float32).unsqueeze(1)
        div_terms = torch.exp(
            torch.arange(0, model_dim, 2, dtype=torch.float32) * (-math.log(10000.0) / model_dim)
        )
        encoding = torch.zeros(max_length, model_dim, dtype=torch.float32)
        encoding[:, 0::2] = torch.sin(positions * div_terms)
        encoding[:, 1::2] = torch.cos(positions * div_terms[: encoding[:, 1::2].shape[1]])

        self.register_buffer("encoding", encoding.unsqueeze(0), persistent=False)

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        if values.ndim != 3:
            raise ValueError("PositionalEncoding expects [batch, sequence, features].")

        sequence_length = values.size(1)
        if sequence_length > self.encoding.size(1):
            raise ValueError(
                f"Sequence length {sequence_length} exceeds maximum {self.encoding.size(1)}."
            )

        return self.dropout(values + self.encoding[:, :sequence_length, :])


class HybridForecaster(nn.Module):
    """LSTM plus Transformer forecaster for multi-step stock price prediction."""

    def __init__(
        self,
        *,
        input_size: int,
        forecast_horizon: int = 7,
        lstm_hidden_size: int = 64,
        lstm_layers: int = 2,
        transformer_layers: int = 2,
        attention_heads: int = 4,
        dropout: float = 0.1,
        max_sequence_length: int = 512,
    ) -> None:
        super().__init__()
        if input_size < 1:
            raise ValueError("input_size must be greater than zero.")
        if forecast_horizon < 1:
            raise ValueError("forecast_horizon must be greater than zero.")
        if lstm_hidden_size % attention_heads != 0:
            raise ValueError("lstm_hidden_size must be divisible by attention_heads.")

        self.input_size = input_size
        self.forecast_horizon = forecast_horizon
        self.lstm_hidden_size = lstm_hidden_size

        # Stage 1: LSTM learns local temporal dynamics from OHLCV sliding windows.
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=lstm_hidden_size,
            num_layers=lstm_layers,
            dropout=dropout if lstm_layers > 1 else 0.0,
            batch_first=True,
        )

        # Stage 2: positional encoding gives the Transformer explicit sequence order.
        self.positional_encoding = PositionalEncoding(
            lstm_hidden_size,
            dropout=dropout,
            max_length=max_sequence_length,
        )

        # Stage 3: TransformerEncoder captures longer-range relationships between days.
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=lstm_hidden_size,
            nhead=attention_heads,
            dim_feedforward=lstm_hidden_size * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=transformer_layers,
        )

        # Stage 4: explicit multi-head attention re-weights encoded time steps before pooling.
        self.temporal_attention = nn.MultiheadAttention(
            embed_dim=lstm_hidden_size,
            num_heads=attention_heads,
            dropout=dropout,
            batch_first=True,
        )
        self.attention_norm = nn.LayerNorm(lstm_hidden_size)

        # Stage 5: regression head maps the final temporal context into the next 7 closes.
        self.forecast_head = nn.Sequential(
            nn.LayerNorm(lstm_hidden_size),
            nn.Linear(lstm_hidden_size, lstm_hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(lstm_hidden_size, forecast_horizon),
        )

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        if values.ndim != 3:
            raise ValueError("HybridForecaster expects [batch, sequence, features].")
        if values.size(-1) != self.input_size:
            raise ValueError(f"Expected {self.input_size} input features, got {values.size(-1)}.")

        lstm_output, _ = self.lstm(values)
        encoded_sequence = self.positional_encoding(lstm_output)
        transformer_output = self.transformer_encoder(encoded_sequence)
        attended_sequence, _ = self.temporal_attention(
            transformer_output,
            transformer_output,
            transformer_output,
            need_weights=False,
        )
        attended_sequence = self.attention_norm(attended_sequence + transformer_output)

        latest_context = attended_sequence[:, -1, :]
        return self.forecast_head(latest_context)