from __future__ import annotations

import json
from pathlib import Path

import joblib
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split

from src.data.preprocess import infer_schema, normalize_target, prepare_features
from src.models.evaluate import evaluate_binary_classifier


def train_model(df, config: dict) -> tuple[CatBoostClassifier, dict, dict]:
    target_column = config["target_column"]
    schema = infer_schema(df, target_column=target_column)
    X = prepare_features(df, schema.feature_columns, schema.categorical_columns)
    y = normalize_target(df[target_column])

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=float(config["test_size"]),
        random_state=int(config["random_state"]),
        stratify=y,
    )

    cat_features = [X.columns.get_loc(col) for col in schema.categorical_columns if col in X.columns]
    model = CatBoostClassifier(
        iterations=int(config["catboost_iterations"]),
        learning_rate=float(config["catboost_learning_rate"]),
        depth=int(config["catboost_depth"]),
        loss_function="Logloss",
        eval_metric="AUC",
        random_seed=int(config["random_state"]),
        verbose=False,
        allow_writing_files=False,
        auto_class_weights="Balanced",
    )
    model.fit(X_train, y_train, cat_features=cat_features, eval_set=(X_test, y_test), use_best_model=True)

    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = evaluate_binary_classifier(y_test, pred, proba)
    metadata = {
        "target_column": schema.target_column,
        "feature_columns": schema.feature_columns,
        "categorical_columns": schema.categorical_columns,
        "display_columns": schema.display_columns,
        "input_columns": schema.input_columns,
        "threshold": 0.5,
        "metrics": metrics,
    }
    return model, metadata, metrics


def save_model_artifacts(model, metadata: dict, config: dict) -> None:
    model_path = Path(config["model_path"])
    metadata_path = Path(config["metadata_path"])
    model_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, model_path)
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
