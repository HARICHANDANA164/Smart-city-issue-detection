"""
Train two ML models:
1) Category model: descriptor -> category
2) Urgency model: descriptor -> urgency_label (Low/Medium/High)

Data handling:
- Input should come from NYC 311 fields:
  - complaint_type
  - descriptor
- We map complaint_type into our 5 categories.
- We generate pseudo urgency labels (since NYC 311 doesn't have them).

Artifacts saved to:
  models/artifacts/category_model.joblib
  models/artifacts/urgency_model.joblib
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


CATEGORIES = [
    "Road & Infrastructure",
    "Water & Drainage",
    "Sanitation",
    "Electricity",
    "Public Safety",
]


COMPLAINT_TYPE_TO_CATEGORY: list[tuple[str, str]] = [
    # Road & Infrastructure
    ("Street Condition", "Road & Infrastructure"),
    ("Sidewalk Condition", "Road & Infrastructure"),
    ("Highway Condition", "Road & Infrastructure"),
    ("Street Sign - Damaged", "Road & Infrastructure"),
    ("Street Sign - Missing", "Road & Infrastructure"),
    # Water & Drainage
    ("Water System", "Water & Drainage"),
    ("Water Quality", "Water & Drainage"),
    ("Sewer", "Water & Drainage"),
    ("Drain", "Water & Drainage"),
    ("Flooding", "Water & Drainage"),
    # Sanitation
    ("Sanitation Condition", "Sanitation"),
    ("Missed Collection", "Sanitation"),
    ("Dirty Conditions", "Sanitation"),
    ("Rodent", "Sanitation"),
    # Electricity
    ("Electric", "Electricity"),
    ("Street Light Condition", "Electricity"),
    # Public Safety
    ("Traffic Signal Condition", "Public Safety"),
    ("Illegal Parking", "Public Safety"),
    ("Noise - Street/Sidewalk", "Public Safety"),
    ("Derelict Vehicle", "Public Safety"),
    ("Blocked Driveway", "Public Safety"),
]


HIGH_KEYWORDS = [
    "leak",
    "danger",
    "outage",
    "sparks",
    "fire",
    "smoke",
    "explosion",
    "gas",
    "overflow",
    "missing cover",
    "accident",
    "injury",
    "hazard",
]

MEDIUM_KEYWORDS = [
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

HIGH_COMPLAINT_TYPES = {
    "Water System",
    "Sewer",
    "Traffic Signal Condition",
    "Electric",
}


def preprocess_text(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\\s]+", " ", text)
    text = re.sub(r"\\s+", " ", text).strip()
    return text


def map_category(complaint_type: str) -> str:
    ct = (complaint_type or "").strip()
    for key, cat in COMPLAINT_TYPE_TO_CATEGORY:
        if ct == key:
            return cat
    # fallback: default bucket (keeps training robust)
    return "Public Safety"


def pseudo_label_urgency(complaint_type: str, descriptor: str) -> str:
    d = preprocess_text(descriptor)
    ct = (complaint_type or "").strip()

    def has_any(keywords: list[str]) -> bool:
        for kw in keywords:
            if re.search(r"\\b" + re.escape(kw) + r"\\b", d):
                return True
        return False

    if ct in HIGH_COMPLAINT_TYPES or has_any(HIGH_KEYWORDS):
        return "High"
    if has_any(MEDIUM_KEYWORDS):
        return "Medium"
    return "Low"


def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    preprocessor=preprocess_text,
                    ngram_range=(1, 2),
                    # keep this demo-friendly (small subsets won't break)
                    min_df=1,
                ),
            ),
            ("clf", LogisticRegression(max_iter=2000)),
        ]
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    in_path = Path(
        os.getenv("TRAIN_INPUT", str(repo_root / "data" / "nyc_311_raw_subset.csv"))
    )
    # If a fully-prepared dataset already exists, you can point TRAIN_INPUT at it.
    out_prepared = Path(
        os.getenv("TRAIN_PREPARED_OUT", str(repo_root / "data" / "nyc_311_subset.csv"))
    )

    category_model_path = Path(
        os.getenv(
            "CATEGORY_MODEL_PATH",
            str(repo_root / "models" / "artifacts" / "category_model.joblib"),
        )
    )
    urgency_model_path = Path(
        os.getenv(
            "URGENCY_MODEL_PATH",
            str(repo_root / "models" / "artifacts" / "urgency_model.joblib"),
        )
    )

    df = pd.read_csv(in_path)
    if "complaint_type" not in df.columns or "descriptor" not in df.columns:
        raise ValueError("Input CSV must have columns: complaint_type, descriptor")

    df["complaint_type"] = df["complaint_type"].astype(str)
    df["descriptor"] = df["descriptor"].astype(str)

    # Step 1: map complaint_type -> category
    df["category"] = df["complaint_type"].apply(map_category)

    # Step 2: pseudo-label urgency
    df["urgency_label"] = df.apply(
        lambda r: pseudo_label_urgency(r["complaint_type"], r["descriptor"]),
        axis=1,
    )

    # Save a prepared dataset for transparency + reproducibility.
    out_prepared.parent.mkdir(parents=True, exist_ok=True)
    df[["complaint_type", "descriptor", "category", "urgency_label"]].to_csv(
        out_prepared, index=False
    )
    print(f"Prepared dataset saved to: {out_prepared}")

    # Step 3: train category model
    cat_model = build_pipeline()
    cat_model.fit(df["descriptor"].tolist(), df["category"].tolist())

    # Step 4: train urgency model
    urg_model = build_pipeline()
    urg_model.fit(df["descriptor"].tolist(), df["urgency_label"].tolist())

    category_model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(cat_model, category_model_path)
    joblib.dump(urg_model, urgency_model_path)

    print(f"Saved category model to: {category_model_path}")
    print(f"Saved urgency model to: {urgency_model_path}")


if __name__ == "__main__":
    main()

