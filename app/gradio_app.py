from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import gradio as gr
except ImportError as exc:
    raise SystemExit("Gradio is not installed. Run: pip install -r requirements.txt") from exc

from src.data.load_data import load_csv
from src.data.preprocess import validate_input_columns
from src.models.predict import filter_previous_month, load_model_artifacts, predict_churn


DATA_PATH = ROOT / "data" / "raw" / "bank_churn_dataset.csv"
MODEL_PATH = ROOT / "models" / "model.pkl"
METADATA_PATH = ROOT / "models" / "metadata.json"

APP_CSS = """
:root {
    --brand: #155e75;
    --brand-strong: #0f3f4f;
    --ink: #172033;
    --muted: #667085;
    --line: #d7dee8;
    --surface: #ffffff;
    --surface-soft: #f5f7fb;
    --risk: #b42318;
    --risk-soft: #fff1f0;
}

.gradio-container {
    max-width: 1280px !important;
    margin: 0 auto !important;
    color: var(--ink);
}

.app-shell {
    padding: 18px 8px 4px;
}

.app-title {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 12px;
}

.app-title h1 {
    margin: 0;
    font-size: 30px;
    line-height: 1.15;
    color: var(--ink);
}

.app-title p {
    margin: 6px 0 0;
    color: var(--muted);
    font-size: 14px;
}

.model-pill {
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: 8px 12px;
    color: var(--brand-strong);
    background: var(--surface-soft);
    font-size: 13px;
    white-space: nowrap;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin: 12px 0 16px;
}

.kpi-card {
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--surface);
    padding: 14px;
}

.kpi-label {
    color: var(--muted);
    font-size: 12px;
    text-transform: uppercase;
}

.kpi-value {
    margin-top: 8px;
    color: var(--ink);
    font-size: 24px;
    font-weight: 700;
}

.kpi-note {
    margin-top: 4px;
    color: var(--muted);
    font-size: 12px;
}

.status-line {
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--surface-soft);
    color: var(--ink);
    padding: 12px 14px;
    font-size: 14px;
}

.status-line strong {
    color: var(--brand-strong);
}

.panel-title {
    margin: 4px 0 8px;
    color: var(--ink);
    font-size: 18px;
    font-weight: 700;
}

button.primary {
    background: var(--brand) !important;
    border-color: var(--brand) !important;
}

@media (max-width: 900px) {
    .app-title {
        display: block;
    }

    .model-pill {
        display: inline-block;
        margin-top: 10px;
    }

    .kpi-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 560px) {
    .kpi-grid {
        grid-template-columns: 1fr;
    }
}
"""


def _load_artifacts():
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError("Model artifacts not found. Run: python -m src.pipelines.run_pipeline")
    return load_model_artifacts(MODEL_PATH, METADATA_PATH)


def _apply_threshold(result: pd.DataFrame, threshold: float) -> pd.DataFrame:
    updated = result.copy()
    updated["predicted_churn"] = updated["churn_probability"] >= threshold
    return updated


def _churn_only(result: pd.DataFrame, threshold: float) -> pd.DataFrame:
    result = _apply_threshold(result, threshold)
    churned = result[result["predicted_churn"]].copy()
    churned["churn_probability"] = (churned["churn_probability"] * 100).round(2)
    churned = churned.rename(
        columns={
            "full_name": "customer_name",
            "last_active_date": "last_active",
            "customer_segment": "segment",
            "churn_probability": "churn_probability_pct",
        }
    )
    return churned


def _metric_value(metadata: dict, key: str) -> str:
    metrics = metadata.get("metrics", {})
    value = metrics.get(key)
    if value is None:
        return "N/A"
    return f"{value:.3f}"


def _summary_html(total: int, churn_count: int, threshold: float, metadata: dict, source: str) -> str:
    churn_rate = (churn_count / total * 100) if total else 0
    return f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Nguon du lieu</div>
            <div class="kpi-value">{source}</div>
            <div class="kpi-note">Tap dang hien thi</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Tong khach hang</div>
            <div class="kpi-value">{total:,}</div>
            <div class="kpi-note">Ban ghi da cham diem</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Du doan churn</div>
            <div class="kpi-value">{churn_count:,}</div>
            <div class="kpi-note">{churn_rate:.2f}% tren tap du lieu</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">ROC-AUC</div>
            <div class="kpi-value">{_metric_value(metadata, "roc_auc")}</div>
            <div class="kpi-note">Nguong hien tai: {threshold:.2f}</div>
        </div>
    </div>
    """


def _status_html(message: str) -> str:
    return f'<div class="status-line">{message}</div>'


def show_previous_month_churn(threshold: float):
    model, metadata = _load_artifacts()
    df = load_csv(DATA_PATH)
    if metadata["target_column"] in df.columns:
        df = df.drop(columns=[metadata["target_column"]])
    previous_month_df = filter_previous_month(df)
    result = predict_churn(previous_month_df, model, metadata)
    churned = _churn_only(result, threshold)
    summary = _summary_html(len(previous_month_df), len(churned), threshold, metadata, "Thang truoc")
    status = _status_html(f"<strong>Da tai xong.</strong> Tim thay {len(churned):,} khach hang co xac suat churn tu {threshold:.0%} tro len.")
    return summary, status, churned


def predict_uploaded_file(file, threshold: float):
    if file is None:
        return (
            _summary_html(0, 0, threshold, {"metrics": {}}, "CSV"),
            _status_html("<strong>Chua co file.</strong> Hay import file CSV de du doan."),
            pd.DataFrame(),
        )

    model, metadata = _load_artifacts()
    df = pd.read_csv(file.name)
    target_column = metadata.get("target_column")
    if target_column in df.columns:
        df = df.drop(columns=[target_column])

    missing = validate_input_columns(df, metadata["input_columns"])
    if missing:
        return (
            _summary_html(0, 0, threshold, metadata, "CSV"),
            _status_html(f"<strong>File khong hop le.</strong> Thieu cac cot bat buoc: {missing}"),
            pd.DataFrame(),
        )

    result = predict_churn(df, model, metadata)
    churned = _churn_only(result, threshold)
    summary = _summary_html(len(df), len(churned), threshold, metadata, "CSV")
    status = _status_html(f"<strong>Da cham diem {len(df):,} khach hang.</strong> Co {len(churned):,} khach hang du doan churn.")
    return summary, status, churned


def _initial_summary():
    try:
        _, metadata = _load_artifacts()
    except FileNotFoundError:
        metadata = {"metrics": {}}
    return _summary_html(0, 0, 0.5, metadata, "San sang")


with gr.Blocks(title="Bank Churn Prediction") as demo:
    gr.HTML(
        """
        <div class="app-shell">
            <div class="app-title">
                <div>
                    <h1>Bank Churn Prediction</h1>
                    <p>Dashboard cham diem churn khach hang bang CatBoost</p>
                </div>
                <div class="model-pill">CatBoost binary classifier</div>
            </div>
        </div>
        """
    )

    summary_html = gr.HTML(_initial_summary())

    with gr.Row():
        threshold_slider = gr.Slider(
            minimum=0.1,
            maximum=0.9,
            value=0.5,
            step=0.05,
            label="Nguong xac suat churn",
        )

    with gr.Tab("Churn thang truoc"):
        gr.HTML('<div class="panel-title">Khach hang co nguy co churn</div>')
        previous_status = gr.HTML(_status_html("San sang tai danh sach churn thang truoc."))
        refresh_btn = gr.Button("Tai danh sach", variant="primary", elem_classes=["primary"])
        previous_month_table = gr.Dataframe(
            interactive=False,
            wrap=True,
        )
        refresh_btn.click(
            show_previous_month_churn,
            inputs=threshold_slider,
            outputs=[summary_html, previous_status, previous_month_table],
        )

    with gr.Tab("Import file du doan"):
        gr.HTML('<div class="panel-title">Cham diem file CSV</div>')
        with gr.Row():
            file_input = gr.File(label="CSV file", file_types=[".csv"])
            predict_btn = gr.Button("Du doan", variant="primary", elem_classes=["primary"])
        upload_status = gr.HTML(_status_html("San sang nhan file CSV."))
        upload_table = gr.Dataframe(
            interactive=False,
            wrap=True,
        )
        predict_btn.click(
            predict_uploaded_file,
            inputs=[file_input, threshold_slider],
            outputs=[summary_html, upload_status, upload_table],
        )


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        prevent_thread_lock=False,
        css=APP_CSS,
        theme=gr.themes.Soft(),
    )
