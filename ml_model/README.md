# ML Model (TF-IDF + Logistic Regression)

This folder contains the training code for the complaint classification model.

## What it does
- Preprocesses text (lowercase + remove special characters)
- Converts text to TF-IDF vectors
- Trains a Logistic Regression classifier
- Saves a single scikit-learn Pipeline as `ml_model/artifacts/model.joblib`

## Train locally

```bash
python ml_model/train.py
```

The script uses `data/sample_issues.csv` by default and writes the model artifact to `ml_model/artifacts/model.joblib`.


