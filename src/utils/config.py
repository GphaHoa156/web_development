from pathlib import Path


DEFAULT_CONFIG = {
    "data_path": "data/raw/bank_churn_dataset.csv",
    "target_column": "exit",
    "model_path": "models/model.pkl",
    "metadata_path": "models/metadata.json",
    "metrics_path": "reports/metrics.json",
    "predictions_path": "reports/predictions.csv",
    "test_size": 0.2,
    "random_state": 42,
    "catboost_iterations": 300,
    "catboost_learning_rate": 0.06,
    "catboost_depth": 6,
}


def _parse_scalar(value: str):
    value = value.strip().strip('"').strip("'")
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_config(config_path: str = "configs/config.yaml") -> dict:
    config = DEFAULT_CONFIG.copy()
    path = Path(config_path)
    if not path.exists():
        return config

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        config[key.strip()] = _parse_scalar(value)
    return config
