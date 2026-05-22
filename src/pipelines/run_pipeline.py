from __future__ import annotations

import json
from pathlib import Path

from src.data.load_data import load_csv
from src.models.predict import predict_churn
from src.models.train import save_model_artifacts, train_model
from src.utils.config import load_config
from src.utils.logger import get_logger


logger = get_logger(__name__)


def main() -> None:
    config = load_config()
    df = load_csv(config["data_path"])
    logger.info("Loaded data with shape %s", df.shape)

    model, metadata, metrics = train_model(df, config)
    save_model_artifacts(model, metadata, config)

    metrics_path = Path(config["metrics_path"])
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    predictions = predict_churn(df.drop(columns=[config["target_column"]]), model, metadata)
    predictions_path = Path(config["predictions_path"])
    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(predictions_path, index=False, encoding="utf-8-sig")

    logger.info("Saved model to %s", config["model_path"])
    logger.info("Metrics: %s", metrics)


if __name__ == "__main__":
    main()
