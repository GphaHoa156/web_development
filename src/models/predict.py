from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from src.data.preprocess import prepare_features, validate_input_columns


def load_model_artifacts(model_path: str | Path = "models/model.pkl", metadata_path: str | Path = "models/metadata.json"):
    model = joblib.load(model_path)
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    return model, metadata


def predict_churn(df: pd.DataFrame, model, metadata: dict) -> pd.DataFrame:
    missing = validate_input_columns(df, metadata["feature_columns"])
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    X = prepare_features(df, metadata["feature_columns"], metadata["categorical_columns"])
    churn_probability = model.predict_proba(X)[:, 1]
    threshold = float(metadata.get("threshold", 0.5))

    display_columns = [col for col in metadata.get("display_columns", []) if col in df.columns]
    result = df[display_columns].copy() if display_columns else pd.DataFrame(index=df.index)
    result["churn_probability"] = churn_probability
    result["predicted_churn"] = churn_probability >= threshold
    return result.sort_values("churn_probability", ascending=False).reset_index(drop=True)


def filter_previous_month(df: pd.DataFrame, date_column: str = "last_active_date") -> pd.DataFrame:
    if date_column not in df.columns:
        return df

    dates = pd.to_datetime(df[date_column], dayfirst=True, errors="coerce")
    if dates.notna().sum() == 0:
        return df

    reference = dates.max()
    previous_month = (reference.to_period("M") - 1)
    mask = dates.dt.to_period("M") == previous_month
    filtered = df.loc[mask].copy()
    return filtered if not filtered.empty else df
