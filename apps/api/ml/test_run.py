import logging
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error

from ml.data_loader import DEFAULT_WEIGHTS_DIR, StockDataLoader
from ml.engine import predict, save_model_weights
from ml.model import HybridForecaster

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class EarlyStopping:
    def __init__(self, patience=5):
        self.patience = patience
        self.counter = 0
        self.best_loss = float('inf')
        self.early_stop = False

    def __call__(self, val_loss):
        if val_loss < self.best_loss:
            self.best_loss = val_loss
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True


def main() -> None:
    ticker = "AAPL"
    scaler_path = DEFAULT_WEIGHTS_DIR / f"{ticker.lower()}_scaler.pkl"
    weights_path = f"{ticker.lower()}_hybrid.pth"

    logging.info(f"Initializing data loader for {ticker}...")
    loader = StockDataLoader()
    
    bundle = loader.create_dataloaders(
        ticker=ticker,
        scaler_path=scaler_path,
        period="2y",  # Using 2 years of data for the quick test
        batch_size=16,
    )

    logging.info(f"Training dataset size: {len(bundle.train_loader.dataset)} windows")
    
    model = HybridForecaster(input_size=len(bundle.feature_columns), forecast_horizon=7)
    
    epochs = 50
    early_stopping = EarlyStopping(patience=5)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = torch.nn.MSELoss()

    print("🚀 Starting real training on AAPL...")

    train_loader = bundle.train_loader
    val_loader = bundle.validation_loader

    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        
        # Training phase
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            predictions = model(X_batch)
            loss = criterion(predictions, y_batch)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        # Validation phase
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for X_val, y_val in val_loader:
                val_preds = model(X_val)
                v_loss = criterion(val_preds, y_val)
                val_loss += v_loss.item()
                
        avg_train_loss = train_loss / len(train_loader)
        avg_val_loss = val_loss / len(val_loader)
        
        print(f"Epoch {epoch+1}/{epochs} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
        
        # Check Early Stopping
        early_stopping(avg_val_loss)
        if early_stopping.early_stop:
            print(f"🛑 Early stopping triggered at Epoch {epoch+1}. The model stopped improving.")
            break

    # Save the fully trained weights
    torch.save(model.state_dict(), "aapl_hybrid_trained.pth")
    print("💾 Trained weights saved to aapl_hybrid_trained.pth")

    # ==========================================
    # 5. EVALUATION AND VISUALIZATION
    # ==========================================
    model.eval()
    actuals = []
    predictions = []

    with torch.no_grad():
        for X_test, y_test in val_loader:
            preds = model(X_test)
            actuals.extend(y_test.numpy())
            predictions.extend(preds.numpy())

    # Un-scale the data back to real dollar amounts!
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

    # Calculate metrics in real dollars
    mae_dollars = mean_absolute_error(actuals_dollars, predictions_dollars)
    rmse_dollars = np.sqrt(mean_squared_error(actuals_dollars, predictions_dollars))

    print("\n💵 Evaluation Metrics (in Real Dollars):")
    print(f"Mean Absolute Error (MAE): ${mae_dollars:.2f}")
    print(f"Root Mean Square Error (RMSE): ${rmse_dollars:.2f}")

    # Plotting the results
    print("📈 Generating the chart... Please check the pop-up window!")
    plt.figure(figsize=(10, 6))
    plt.plot(actuals_dollars, label="Actual AAPL Price", color="blue")
    plt.plot(predictions_dollars, label="Predicted AAPL Price", color="orange", linestyle="--")
    plt.title("AAPL 7-Day Forecast vs Actual Prices")
    plt.xlabel("Time (Days in Test Set)")
    plt.ylabel("Price (USD)")
    plt.legend()
    plt.grid(True)

    # Save the chart as an image so it doesn't freeze the process
    plt.savefig("chart.png")
    print("📈 Chart saved to apps/api/chart.png!")

if __name__ == "__main__":
    main()