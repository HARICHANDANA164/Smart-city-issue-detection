"""
Train a simple NLP classifier for smart-city complaints.

Model:
  - TF-IDF
  - Logistic Regression

Output:
  - A single scikit-learn Pipeline saved to: ml_model/artifacts/model.joblib

This is intentionally small + readable for demos and easy AWS migration later.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def preprocess_text(text: str) -> str:
    """
    Very lightweight preprocessing (as requested):
    - lowercase
    - remove special characters (keep letters/numbers/spaces)
    """
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    preprocessor=preprocess_text,
                    ngram_range=(1, 2),
                    min_df=1,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    n_jobs=None,  # keep compatible across platforms
                ),
            ),
        ]
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    data_path = Path(
        os.getenv("TRAIN_DATA_PATH", str(repo_root / "data" / "sample_issues.csv"))
    )
    out_path = Path(
        os.getenv("MODEL_PATH", str(repo_root / "ml_model" / "artifacts" / "model.joblib"))
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    if "text" not in df.columns or "category" not in df.columns:
        raise ValueError("Training data must have columns: text, category")

    X = df["text"].astype(str).tolist()
    y = df["category"].astype(str).tolist()

    pipeline = build_pipeline()
    pipeline.fit(X, y)

    joblib.dump(pipeline, out_path)
    print(f"Saved model to: {out_path}")


if __name__ == "__main__":
    main()


