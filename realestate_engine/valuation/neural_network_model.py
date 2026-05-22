"""Neural Network model for property valuation.

Deep learning model with configurable architecture for capturing
complex non-linear relationships in property pricing.
"""
import math
import os
import pickle
import numpy as np
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timezone
from loguru import logger

try:
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn not available, NeuralNetwork model disabled")

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    optim = None  # type: ignore[assignment]
    DataLoader = None  # type: ignore[assignment]
    TensorDataset = None  # type: ignore[assignment]
    TORCH_AVAILABLE = False
    logger.warning("torch not available, NeuralNetwork model disabled")

from realestate_engine.database.repository import DatabaseRepository

UTC = timezone.utc


if TORCH_AVAILABLE:
    class PropertyNN(nn.Module):
        """Neural network architecture for property valuation."""

        def __init__(self, input_dim: int, hidden_dims: List[int] = None, dropout: float = 0.3):
            super().__init__()
            hidden_dims = hidden_dims or [256, 128, 64]

            layers = []
            prev_dim = input_dim
            for h_dim in hidden_dims:
                layers.extend([
                    nn.Linear(prev_dim, h_dim),
                    nn.BatchNorm1d(h_dim),
                    nn.ReLU(),
                    nn.Dropout(dropout),
                ])
                prev_dim = h_dim

            layers.append(nn.Linear(prev_dim, 1))
            self.network = nn.Sequential(*layers)

        def forward(self, x):
            return self.network(x)


class NeuralNetworkModel:
    """Neural Network valuation model with PyTorch backend."""

    def __init__(self, repo: Optional[DatabaseRepository] = None):
        self.repo = repo or DatabaseRepository()
        self.model: Optional[PropertyNN] = None
        self.scaler: Optional[StandardScaler] = None
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.feature_names: List[str] = []
        self.input_dim: int = 0
        self.is_trained = False
        self.model_version: Optional[str] = None
        self.training_metrics: Dict = {}

    @property
    def available(self) -> bool:
        return SKLEARN_AVAILABLE and TORCH_AVAILABLE

    def _prepare_features(self, listings: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        features = []
        prices = []

        for listing in listings:
            feats = [
                float(listing.get("area_util_m2", 0)),
                float(listing.get("quartos", 0)),
                float(listing.get("casas_banho", 0)),
                float(listing.get("ano_construcao", 2000)),
                float(listing.get("dist_metro_m", 1000)),
                float(listing.get("dist_escola_m", 500)),
                float(listing.get("dist_comercio_m", 500)),
                float(listing.get("lat", 0)),
                float(listing.get("lon", 0)),
                1.0 if listing.get("tem_garagem") else 0.0,
                1.0 if listing.get("tem_elevador") else 0.0,
                1.0 if listing.get("tem_piscina") else 0.0,
            ]
            features.append(feats)
            prices.append(float(listing.get("preco_pedido", 0)))

        return np.array(features, dtype=np.float32), np.array(prices, dtype=np.float32)

    def train(self, listings: List[Dict], epochs: int = 100, batch_size: int = 32,
              learning_rate: float = 0.001, validation_split: float = 0.2) -> Dict:
        if not self.available:
            logger.warning("NeuralNetwork dependencies not available, skipping training")
            return {"status": "unavailable"}

        if len(listings) < 50:
            logger.warning(f"Insufficient data for NN training: {len(listings)} listings")
            return {"status": "insufficient_data"}

        X, y = self._prepare_features(listings)
        self.input_dim = X.shape[1]
        self.feature_names = [
            "area_util_m2", "quartos", "casas_banho", "ano_construcao",
            "dist_metro_m", "dist_escola_m", "dist_comercio_m",
            "lat", "lon", "tem_garagem", "tem_elevador", "tem_piscina",
        ]

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y, test_size=validation_split, random_state=42
        )

        train_dataset = TensorDataset(
            torch.FloatTensor(X_train), torch.FloatTensor(y_train).reshape(-1, 1)
        )
        val_dataset = TensorDataset(
            torch.FloatTensor(X_val), torch.FloatTensor(y_val).reshape(-1, 1)
        )
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)

        self.model = PropertyNN(input_dim=self.input_dim)
        criterion = nn.HuberLoss(delta=50000)
        optimizer = optim.AdamW(self.model.parameters(), lr=learning_rate, weight_decay=1e-4)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=10, factor=0.5)

        best_val_loss = float('inf')
        patience_counter = 0
        max_patience = 20

        for epoch in range(epochs):
            self.model.train()
            train_loss = 0.0
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                pred = self.model(batch_X)
                loss = criterion(pred, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                train_loss += loss.item()

            self.model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    pred = self.model(batch_X)
                    loss = criterion(pred, batch_y)
                    val_loss += loss.item()

            avg_train_loss = train_loss / len(train_loader)
            avg_val_loss = val_loss / len(val_loader)
            scheduler.step(avg_val_loss)

            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
            else:
                patience_counter += 1

            if patience_counter >= max_patience:
                logger.info(f"NN early stopping at epoch {epoch}")
                break

        self.is_trained = True
        self.model_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        self.training_metrics = {
            "final_train_loss": avg_train_loss,
            "final_val_loss": avg_val_loss,
            "best_val_loss": best_val_loss,
            "epochs_completed": epoch + 1,
            "n_samples": len(listings),
        }

        logger.info(f"NN trained: val_loss={best_val_loss:.2f}, epochs={epoch+1}")
        return self.training_metrics

    def predict(self, listing: Dict) -> Optional[float]:
        if not self.is_trained or not self.model:
            return None

        feats = np.array([[
            float(listing.get("area_util_m2", 0)),
            float(listing.get("quartos", 0)),
            float(listing.get("casas_banho", 0)),
            float(listing.get("ano_construcao", 2000)),
            float(listing.get("dist_metro_m", 1000)),
            float(listing.get("dist_escola_m", 500)),
            float(listing.get("dist_comercio_m", 500)),
            float(listing.get("lat", 0)),
            float(listing.get("lon", 0)),
            1.0 if listing.get("tem_garagem") else 0.0,
            1.0 if listing.get("tem_elevador") else 0.0,
            1.0 if listing.get("tem_piscina") else 0.0,
        ]], dtype=np.float32)

        feats_scaled = self.scaler.transform(feats)
        self.model.eval()
        with torch.no_grad():
            pred = self.model(torch.FloatTensor(feats_scaled))
            return float(pred.item())

    def predict_batch(self, listings: List[Dict]) -> List[Optional[float]]:
        return [self.predict(l) for l in listings]

    def save(self, path: str):
        if not self.is_trained:
            return
        state = {
            "model_state": self.model.state_dict(),
            "scaler": self.scaler,
            "input_dim": self.input_dim,
            "feature_names": self.feature_names,
            "version": self.model_version,
            "metrics": self.training_metrics,
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(state, path)
        logger.info(f"NN model saved to {path}")

    def load(self, path: str):
        if not os.path.exists(path):
            logger.warning(f"NN model not found at {path}")
            return False
        state = torch.load(path, map_location="cpu")
        self.scaler = state["scaler"]
        self.input_dim = state["input_dim"]
        self.feature_names = state["feature_names"]
        self.model_version = state["version"]
        self.training_metrics = state.get("metrics", {})
        self.model = PropertyNN(input_dim=self.input_dim)
        self.model.load_state_dict(state["model_state"])
        self.model.eval()
        self.is_trained = True
        logger.info(f"NN model loaded from {path} (v{self.model_version})")
        return True
