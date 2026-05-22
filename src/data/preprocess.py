from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


TARGET_COLUMN = "exit"
DISPLAY_COLUMNS = ["id", "full_name", "last_active_date", "customer_segment"]
DROP_FEATURE_COLUMNS = ["id", "full_name"]


@dataclass
class DatasetSchema:
    target_column: str
    feature_columns: list[str]
    categorical_columns: list[str]
    display_columns: list[str]
    input_columns: list[str]


def normalize_target(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.astype(int)
    lowered = series.astype(str).str.strip().str.lower()
    return lowered.map({"true": 1, "false": 0, "1": 1, "0": 0, "yes": 1, "no": 0}).fillna(series).astype(int)


def infer_schema(df: pd.DataFrame, target_column: str = TARGET_COLUMN) -> DatasetSchema:
    if target_column not in df.columns:
        raise ValueError(f"Missing target column: {target_column}")

    feature_columns = [col for col in df.columns if col != target_column and col not in DROP_FEATURE_COLUMNS]
    categorical_columns = [
        col
        for col in feature_columns
        if (
            pd.api.types.is_object_dtype(df[col])
            or pd.api.types.is_string_dtype(df[col])
            or pd.api.types.is_categorical_dtype(df[col])
            or pd.api.types.is_bool_dtype(df[col])
        )
    ]
    display_columns = [col for col in DISPLAY_COLUMNS if col in df.columns]
    input_columns = [col for col in df.columns if col != target_column]
    return DatasetSchema(
        target_column=target_column,
        feature_columns=feature_columns,
        categorical_columns=categorical_columns,
        display_columns=display_columns,
        input_columns=input_columns,
    )


def prepare_features(df: pd.DataFrame, feature_columns: list[str], categorical_columns: list[str]) -> pd.DataFrame:
    missing = [col for col in feature_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    features = df[feature_columns].copy()
    for col in categorical_columns:
        if col in features.columns:
            features[col] = features[col].fillna("missing").astype(str)
    return features


def validate_input_columns(df: pd.DataFrame, required_columns: list[str]) -> list[str]:
    return [col for col in required_columns if col not in df.columns]
