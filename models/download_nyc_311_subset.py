"""
Download a small NYC 311 subset using NYC Open Data (Socrata).

This creates a CSV with:
  - complaint_type
  - descriptor

You can then run `train_models.py` to:
  - map complaint_type -> our 5 categories
  - generate pseudo urgency labels
  - train two ML models (category + urgency)

Notes:
- Requires internet access.
- The dataset behind this endpoint is the NYC 311 Service Requests dataset.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import requests


NYC_311_ENDPOINT = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    out_path = Path(os.getenv("NYC_311_OUT", str(repo_root / "data" / "nyc_311_raw_subset.csv")))
    limit = int(os.getenv("NYC_311_LIMIT", "2000"))

    params = {
        "$select": "complaint_type,descriptor",
        "$limit": limit,
        # keep rows with non-empty descriptor
        "$where": "descriptor IS NOT NULL",
    }

    print(f"Fetching {limit} rows from NYC 311 ...")
    resp = requests.get(NYC_311_ENDPOINT, params=params, timeout=60)
    resp.raise_for_status()
    rows = resp.json()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["complaint_type", "descriptor"])
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "complaint_type": (r.get("complaint_type") or "").strip(),
                    "descriptor": (r.get("descriptor") or "").strip(),
                }
            )

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()

