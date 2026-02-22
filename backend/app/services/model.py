from __future__ import annotations

"""
Model loader for the complaint classifier + urgency classifier.

Cloud-friendly behavior:
- Prefer loading a saved artifact (fast, deterministic).
- If missing, train quickly from a small NYC 311 subset CSV and persist artifacts.

This keeps the API stateless: the prediction does not depend on server state,
only on the complaint text and the saved model artifacts.
"""

from pathlib import Path

import joblib
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .preprocess import preprocess_text


_COMPLAINT_TYPE_TO_CATEGORY: list[tuple[str, str]] = [
    ("Street Condition", "Road & Infrastructure"),
    ("Sidewalk Condition", "Road & Infrastructure"),
    ("Highway Condition", "Road & Infrastructure"),
    ("Street Sign - Damaged", "Road & Infrastructure"),
    ("Street Sign - Missing", "Road & Infrastructure"),
    ("Water System", "Water & Drainage"),
    ("Water Quality", "Water & Drainage"),
    ("Sewer", "Water & Drainage"),
    ("Drain", "Water & Drainage"),
    ("Flooding", "Water & Drainage"),
    ("Sanitation Condition", "Sanitation"),
    ("Missed Collection", "Sanitation"),
    ("Dirty Conditions", "Sanitation"),
    ("Rodent", "Sanitation"),
    ("Electric", "Electricity"),
    ("Street Light Condition", "Electricity"),
    ("Traffic Signal Condition", "Public Safety"),
    ("Illegal Parking", "Public Safety"),
    ("Noise - Street/Sidewalk", "Public Safety"),
    ("Derelict Vehicle", "Public Safety"),
    ("Blocked Driveway", "Public Safety"),
]

_HIGH_KEYWORDS = [
    "leak",
    "danger",
    "outage",
    "sparks",
    "fire",
    "smoke",
    "explosion",
    "gas",
    "overflow",
    "accident",
    "injury",
    "hazard",
]

_MEDIUM_KEYWORDS = [
    "not working",
    "broken",
    "delay",
    "clogged",
    "blocked",
    "cuts",
    "power cut",
    "dark",
    "unsafe",
    "voltage",
]

_HIGH_COMPLAINT_TYPES = {"Water System", "Sewer", "Traffic Signal Condition", "Electric"}


def _build_pipeline() -> Pipeline:
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
                    n_jobs=None,
                ),
            ),
        ]
    )


def _map_category(complaint_type: str) -> str:
    ct = (complaint_type or "").strip()
    for key, cat in _COMPLAINT_TYPE_TO_CATEGORY:
        if ct == key:
            return cat
    return "Public Safety"


def _pseudo_label_urgency(complaint_type: str, descriptor: str) -> str:
    d = preprocess_text(descriptor)
    ct = (complaint_type or "").strip()

    def has_any(keywords: list[str]) -> bool:
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", d):
                return True
        return False

    if ct in _HIGH_COMPLAINT_TYPES or has_any(_HIGH_KEYWORDS):
        return "High"
    if has_any(_MEDIUM_KEYWORDS):
        return "Medium"
    return "Low"


def _prepare_training_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Accept either:
    - prepared CSV: complaint_type, descriptor, category, urgency_label
    - raw CSV: complaint_type, descriptor
    and ensure category + urgency_label exist.
    """
    if "descriptor" not in df.columns:
        raise ValueError("Training data must have column: descriptor")

    # If complaint_type missing, treat as unknown (still trainable for demo).
    if "complaint_type" not in df.columns:
        df["complaint_type"] = ""

    df["complaint_type"] = df["complaint_type"].astype(str)
    df["descriptor"] = df["descriptor"].astype(str)

    if "category" not in df.columns:
        df["category"] = df["complaint_type"].apply(_map_category)
    if "urgency_label" not in df.columns:
        df["urgency_label"] = df.apply(
            lambda r: _pseudo_label_urgency(r["complaint_type"], r["descriptor"]),
            axis=1,
        )

    return df


def train_and_save_model(train_data_path: Path, model_path: Path, label_col: str) -> Pipeline:
    df = _prepare_training_df(pd.read_csv(train_data_path))
    if label_col not in df.columns:
        raise ValueError(f"Training data must have column: {label_col}")

    X = df["descriptor"].astype(str).tolist()
    y = df[label_col].astype(str).tolist()

    pipeline = _build_pipeline()
    pipeline.fit(X, y)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    return pipeline


def load_or_train_model(train_data_path: Path, model_path: Path, label_col: str) -> Pipeline:
    if model_path.exists():
        return joblib.load(model_path)
    return train_and_save_model(
        train_data_path=train_data_path,
        model_path=model_path,
        label_col=label_col,
    )


def load_models(
    train_data_path: Path,
    category_model_path: Path,
    urgency_model_path: Path,
) -> tuple[Pipeline, Pipeline]:
    """
    Returns (category_model, urgency_model).

    Expects the training CSV to contain:
    - descriptor
    - category
    - urgency_label
    """
    category_model = load_or_train_model(
        train_data_path=train_data_path,
        model_path=category_model_path,
        label_col="category",
    )
    urgency_model = load_or_train_model(
        train_data_path=train_data_path,
        model_path=urgency_model_path,
        label_col="urgency_label",
    )
    return category_model, urgency_model

