# Bank Churn Prediction

Du an du doan khach hang churn bang CatBoost va giao dien Gradio don gian.

## Cau truc

- `data/raw/`: du lieu goc.
- `src/`: code xu ly du lieu, train, predict, evaluate.
- `models/`: model da train va metadata schema.
- `reports/`: metrics va figures.
- `app/gradio_app.py`: giao dien import file va hien thi khach hang du doan churn.

## Cai dat

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

## Train model

```powershell
.\.venv\Scripts\python.exe -m src.pipelines.run_pipeline
```

Ket qua mac dinh:

- `models/model.pkl`
- `models/metadata.json`
- `reports/metrics.json`
- `reports/predictions.csv`

## Chay app Gradio

```powershell
.\.venv\Scripts\python.exe app\gradio_app.py
```

App co the day len Hugging Face Spaces. Can dam bao `requirements.txt`, `app/gradio_app.py`, `src/`, `models/model.pkl`, va `models/metadata.json` co trong repo/Space.
