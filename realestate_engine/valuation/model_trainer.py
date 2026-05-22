"""Professional model training with proper validation to prevent overfitting."""
from __future__ import annotations

import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.model_selection import train_test_split, TimeSeriesSplit, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from loguru import logger


class ModelTrainer:
    """Professional model training with proper validation."""

    MIN_LISTINGS = 100  # Increased from 10 to ensure sufficient data

    def __init__(
        self,
        test_size: float = 0.2,
        random_state: int = 42,
        time_series_split: bool = True
    ):
        self.test_size = test_size
        self.random_state = random_state
        self.time_series_split = time_series_split  # For temporal data
        self.evaluation_results: Dict[str, Dict] = {}

    def split_data(self, listings: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Split data into train and test sets.

        For real estate, use time-series split (older data for training,
        newer data for testing) to avoid data leakage.
        """
        if len(listings) < self.MIN_LISTINGS:
            raise ValueError(
                f"Insufficient data for training: {len(listings)} < {self.MIN_LISTINGS}. "
                f"Need at least {self.MIN_LISTINGS} listings."
            )

        if self.time_series_split:
            # Sort by scrape_timestamp
            sorted_listings = sorted(
                listings,
                key=lambda x: x.get('scrape_timestamp', '')
            )

            # Use last 20% for testing
            split_idx = int(len(sorted_listings) * (1 - self.test_size))
            train = sorted_listings[:split_idx]
            test = sorted_listings[split_idx:]

            logger.info(
                f"Time-series split: train={len(train)}, test={len(test)} "
                f"(test date range: {test[0].get('scrape_timestamp')} to {test[-1].get('scrape_timestamp')})"
            )
        else:
            # Random split (use with caution for temporal data)
            train, test = train_test_split(
                listings,
                test_size=self.test_size,
                random_state=self.random_state
            )
            logger.info(f"Random split: train={len(train)}, test={len(test)}")

        return train, test

    def train_and_evaluate(
        self,
        model,
        train_data: List[Dict],
        test_data: List[Dict],
        model_name: str
    ) -> Dict:
        """Train model and evaluate on test set."""
        # Train
        model.train(train_data)

        # Predict on train
        train_predictions = [
            model.predict(listing)
            for listing in train_data
        ]
        train_actuals = [
            listing.get('preco_pedido')
            for listing in train_data
        ]

        # Predict on test
        test_predictions = [
            model.predict(listing)
            for listing in test_data
        ]
        test_actuals = [
            listing.get('preco_pedido')
            for listing in test_data
        ]

        # Calculate metrics
        train_mae = mean_absolute_error(train_actuals, train_predictions)
        train_rmse = np.sqrt(mean_squared_error(train_actuals, train_predictions))
        train_r2 = r2_score(train_actuals, train_predictions)

        test_mae = mean_absolute_error(test_actuals, test_predictions)
        test_rmse = np.sqrt(mean_squared_error(test_actuals, test_predictions))
        test_r2 = r2_score(test_actuals, test_predictions)

        results = {
            "model_name": model_name,
            "train_mae": train_mae,
            "train_rmse": train_rmse,
            "train_r2": train_r2,
            "test_mae": test_mae,
            "test_rmse": test_rmse,
            "test_r2": test_r2,
            "overfitting": (train_r2 - test_r2) > 0.1,  # Threshold for overfitting
        }

        self.evaluation_results[model_name] = results

        logger.info(
            f"{model_name} - Train: MAE={train_mae:.0f}€, RMSE={train_rmse:.0f}€, R²={train_r2:.3f} | "
            f"Test: MAE={test_mae:.0f}€, RMSE={test_rmse:.0f}€, R²={test_r2:.3f}"
        )

        if results["overfitting"]:
            logger.warning(
                f"{model_name} shows signs of overfitting "
                f"(R² gap: {train_r2 - test_r2:.3f})"
            )

        return results

    def detect_overfitting(self, train_mae: float, test_mae: float, threshold: float = 0.5) -> bool:
        """Detect overfitting when test MAE is significantly higher than train MAE.

        Returns True if (test_mae - train_mae) / train_mae > threshold.
        """
        if train_mae <= 0:
            return False
        return (test_mae - train_mae) / train_mae > threshold

    def evaluate(self, y_true, y_pred) -> Dict:
        """Calculate evaluation metrics from true and predicted values."""
        return {
            "mae": mean_absolute_error(y_true, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
            "r2": r2_score(y_true, y_pred),
        }

    def cross_validate(
        self,
        model,
        data: List[Dict],
        n_splits: int = 5
    ) -> Dict:
        """Perform k-fold cross-validation."""
        if self.time_series_split:
            # Use TimeSeriesSplit for temporal data
            tscv = TimeSeriesSplit(n_splits=n_splits)
        else:
            tscv = KFold(
                n_splits=n_splits,
                shuffle=True,
                random_state=self.random_state
            )

        mae_scores = []
        rmse_scores = []
        r2_scores = []

        for fold, (train_idx, test_idx) in enumerate(tscv.split(data)):
            train = [data[i] for i in train_idx]
            test = [data[i] for i in test_idx]

            # Train and evaluate
            results = self.train_and_evaluate(
                model,
                train,
                test,
                f"{model.__class__.__name__}_fold{fold}"
            )

            mae_scores.append(results["test_mae"])
            rmse_scores.append(results["test_rmse"])
            r2_scores.append(results["test_r2"])

        cv_results = {
            "mae_mean": np.mean(mae_scores),
            "mae_std": np.std(mae_scores),
            "rmse_mean": np.mean(rmse_scores),
            "rmse_std": np.std(rmse_scores),
            "r2_mean": np.mean(r2_scores),
            "r2_std": np.std(r2_scores),
        }

        logger.info(
            f"Cross-validation results: MAE={cv_results['mae_mean']:.0f}±{cv_results['mae_std']:.0f}€, "
            f"RMSE={cv_results['rmse_mean']:.0f}±{cv_results['rmse_std']:.0f}€, "
            f"R²={cv_results['r2_mean']:.3f}±{cv_results['r2_std']:.3f}"
        )

        return cv_results

    def get_evaluation_summary(self) -> Dict:
        """Get summary of all evaluation results."""
        if not self.evaluation_results:
            return {}

        summary = {
            "num_models": len(self.evaluation_results),
            "models": {}
        }

        for model_name, results in self.evaluation_results.items():
            summary["models"][model_name] = {
                "test_mae": results["test_mae"],
                "test_rmse": results["test_rmse"],
                "test_r2": results["test_r2"],
                "overfitting": results["overfitting"]
            }

        return summary

    def clear_results(self):
        """Clear evaluation results."""
        self.evaluation_results.clear()
