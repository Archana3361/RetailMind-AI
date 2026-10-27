import pandas as pd
import joblib

from pathlib import Path


class DemandPredictionService:

    def __init__(self):

        # ------------------------------------------
        # Project paths
        # ------------------------------------------

        base_dir = Path(__file__).resolve().parent.parent

        model_dir = base_dir / "models"

        # ------------------------------------------
        # Load trained model
        # ------------------------------------------

        self.model = joblib.load(
            model_dir / "best_model.pkl"
        )

        # ------------------------------------------
        # Load preprocessing pipeline
        # ------------------------------------------

        self.preprocessor = joblib.load(
            model_dir / "preprocessor.pkl"
        )

        # ------------------------------------------
        # Load feature list
        # ------------------------------------------

        self.feature_columns = joblib.load(
            model_dir / "feature_columns.pkl"
        )

    def predict(self, input_data):

        """
        Predict demand for one or more records.

        input_data must contain all feature columns
        used during model training.
        """

        # Convert input into DataFrame

        df = pd.DataFrame(input_data)

        # Make sure columns are in the same order
        # as during training

        df = df[
            self.feature_columns
        ]

        # Apply saved preprocessing

        X = self.preprocessor.transform(
            df
        )

        # Generate prediction

        prediction = self.model.predict(
            X
        )

        # Demand cannot be negative

        prediction = prediction.clip(
            min=0
        )

        return prediction