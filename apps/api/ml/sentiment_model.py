import logging
from pathlib import Path
import torch
from torch import nn

logger = logging.getLogger(__name__)

class SentimentImpactPredictor(nn.Module):
    """
    An MLP taking features such as score, impact_weight, and article_count,
    passing through linear layers with ReLU/Dropout to output a single 
    continuous sentiment impact score or signal.
    """
    def __init__(self, input_features: int = 3, hidden_dim: int = 16, dropout: float = 0.2):
        super().__init__()
        self.input_features = input_features
        self.net = nn.Sequential(
            nn.Linear(input_features, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x shape: [batch_size, input_features]
        Returns shape: [batch_size, 1]
        """
        return self.net(x)


def load_sentiment_model(
    model_path: Path, 
    device: torch.device = None
) -> SentimentImpactPredictor:
    """
    Loads the SentimentImpactPredictor model. If the pre-trained .pt file
    is not found, initializes default weights and logs a warning.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    model = SentimentImpactPredictor()
    
    if model_path.exists():
        try:
            model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
            logger.info(f"Loaded sentiment model weights from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load sentiment model weights from {model_path}: {e}")
            logger.warning("Initializing with default random weights as fallback.")
    else:
        logger.warning(
            f"Pre-trained sentiment model not found at {model_path}. "
            "Initializing with default random weights as fallback."
        )
        
    model.to(device)
    model.eval()
    return model
