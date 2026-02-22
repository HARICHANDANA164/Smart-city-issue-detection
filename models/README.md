# Models (2x ML: Category + Urgency)

This project trains **two** scikit-learn text classifiers (TF‑IDF + Logistic Regression):

- **Model 1**: predicts **category**
- **Model 2**: predicts **urgency** (`Low` / `Medium` / `High`)

Both models use NYC 311 dataset fields:
- `complaint_type`
- `descriptor` (free text)

Because NYC 311 has no urgency label, we generate a **pseudo-label** `urgency_label` using keyword + complaint_type heuristics, then train Model 2 on that label.

## Option A: Use the included prepared sample

The repo already includes `data/nyc_311_subset.csv` (small demo subset) so you can train immediately.

## Option B: Download a bigger subset (recommended)

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r models/requirements.txt

python models/download_nyc_311_subset.py
```

This saves `data/nyc_311_raw_subset.csv`.

## Train both models

```bash
python models/train_models.py
```

Artifacts are saved to:
- `models/artifacts/category_model.joblib`
- `models/artifacts/urgency_model.joblib`

