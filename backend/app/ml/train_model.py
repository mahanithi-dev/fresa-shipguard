from pathlib import Path
from datetime import date

import pandas as pd
from joblib import dump
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

from app.db import SessionLocal
from app.entities import Shipment
from app.ml.features import build_feature_dict, label_from_shipment


def build_dataset(db):
    today = date.today()
    shipments = (
        db.query(Shipment)
        .filter(Shipment.etd.isnot(None), Shipment.eta.isnot(None), Shipment.actual_arrival.isnot(None))
        .all()
    )
    rows = []
    labels = []
    for s in shipments:
        # only train on shipments with ETD in the past (completed)
        if s.etd and s.etd >= today:
            continue
        features = build_feature_dict(db, s)
        rows.append(features)
        labels.append(label_from_shipment(s))
    if not rows:
        return None, None
    df = pd.DataFrame(rows)
    y = pd.Series(labels)
    return df, y


def train_and_save():
    db = SessionLocal()
    try:
        X, y = build_dataset(db)
        if X is None or X.empty:
            print("No training data available.")
            return

        # One-hot encode categorical features
        X_proc = pd.get_dummies(X, columns=["mode", "cargo_type", "month_of_etd"], drop_first=True)

        X_train, X_test, y_train, y_test = train_test_split(X_proc, y, test_size=0.2, random_state=42)

        model = LogisticRegression(max_iter=1000)
        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

        metrics = {
            "precision": float(precision_score(y_test, preds, zero_division=0)),
            "recall": float(recall_score(y_test, preds, zero_division=0)),
            "f1_score": float(f1_score(y_test, preds, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_test, probs)) if probs is not None else None,
            "n_samples": int(len(X_proc)),
        }

        out = {
            "model": model,
            "feature_columns": list(X_proc.columns),
            "metrics": metrics,
        }

        path = Path(__file__).with_name("model.joblib")
        dump(out, path)
        print(f"Saved model to {path}")
        print("Metrics:", metrics)
    finally:
        db.close()


if __name__ == "__main__":
    train_and_save()
