import os
import pickle
from datetime import date
from typing import Optional

import pandas as pd
from fastapi import HTTPException

from config import DATA_DIR, MODELS_DIR

df:        Optional[pd.DataFrame] = None
models:    dict = {}
scalers:   dict = {}
metadatas: dict = {}


def load_data():
    global df
    path = os.path.join(DATA_DIR, "merged.csv")
    df   = pd.read_csv(path, parse_dates=["Date"])
    print(f"[startup] Data loaded: {len(df):,} rows, {df['Symbol'].nunique()} symbols")


def load_models():
    for model_type in ("single", "multi"):
        path = os.path.join(MODELS_DIR, model_type)
        with open(os.path.join(path, "best_model.pkl"), "rb") as f:
            models[model_type] = pickle.load(f)
        with open(os.path.join(path, "scaler.pkl"), "rb") as f:
            scalers[model_type] = pickle.load(f)
        with open(os.path.join(path, "metadata.pkl"), "rb") as f:
            metadatas[model_type] = pickle.load(f)
        print(f"[startup] Loaded {model_type} model | features: {metadatas[model_type]['feature_cols']}")


def get_symbols() -> list:
    assert df is not None, "Data not loaded - call load_data() first"
    return sorted(df["Symbol"].unique().tolist())


def get_feature_cols(model_type: str) -> list:
    return metadatas[model_type]["feature_cols"]


def get_window(symbol: str, target_date: date, model_type: str) -> pd.DataFrame:
    assert df is not None, "Data not loaded - call load_data() first"
    window_size = metadatas[model_type]["window_size"]
    sym_df      = df[df["Symbol"] == symbol].sort_values("Date")
    before      = sym_df[sym_df["Date"] < pd.Timestamp(target_date)]

    if len(before) < window_size:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough history for {symbol} before {target_date}. Need {window_size} days, have {len(before)}."
        )
    return before.tail(window_size)


def get_trading_dates(symbol: str, start: date, end: date) -> list:
    assert df is not None, "Data not loaded - call load_data() first"
    sym_df = df[df["Symbol"] == symbol].sort_values("Date")
    return sym_df[
        (sym_df["Date"] >= pd.Timestamp(start)) &
        (sym_df["Date"] <= pd.Timestamp(end))
    ]["Date"].tolist()


def get_daily_return(symbol: str, target_date: date) -> Optional[float]:
    assert df is not None, "Data not loaded - call load_data() first"
    row = df[(df["Symbol"] == symbol) & (df["Date"] == pd.Timestamp(target_date))]
    if row.empty:
        return None
    return float(row.iloc[0]["daily_return"])


def get_actual(symbol: str, target_date: date) -> Optional[str]:
    assert df is not None, "Data not loaded - call load_data() first"
    row = df[(df["Symbol"] == symbol) & (df["Date"] == pd.Timestamp(target_date))]
    if row.empty:
        return None
    return "UP" if float(row.iloc[0]["daily_return"]) > 0 else "DOWN"


def run_prediction(X_raw, model_type: str):
    """Single prediction. X_raw shape: (window_size, n_features) - unscaled."""
    feature_cols = metadatas[model_type]["feature_cols"]
    window_size  = metadatas[model_type]["window_size"]
    X_scaled     = scalers[model_type].transform(X_raw)
    X_input      = X_scaled.reshape(1, window_size, len(feature_cols))
    raw_prob     = float(models[model_type].predict(X_input, verbose=0).flatten()[0])
    prediction   = "UP" if raw_prob > 0.5 else "DOWN"
    confidence   = round(raw_prob if raw_prob > 0.5 else 1 - raw_prob, 4)
    return prediction, confidence, raw_prob


def batch_predict(X_batch, model_type: str):
    """Run all windows through the model in one call.

    X_batch shape: (n_dates, window_size, n_features) - unscaled values.
    Returns (predictions, confidences) as lists.
    """
    feature_cols = metadatas[model_type]["feature_cols"]
    window_size  = metadatas[model_type]["window_size"]
    n_dates      = X_batch.shape[0]

    # Scale: flatten to (n_dates * window_size, n_features), scale, reshape back
    X_flat    = X_batch.reshape(n_dates * window_size, len(feature_cols))
    X_scaled  = scalers[model_type].transform(X_flat)
    X_input   = X_scaled.reshape(n_dates, window_size, len(feature_cols))

    raw_probs   = models[model_type].predict(X_input, verbose=0).flatten()
    predictions = ["UP" if p > 0.5 else "DOWN" for p in raw_probs]
    confidences = [round(float(p if p > 0.5 else 1 - p), 4) for p in raw_probs]
    return predictions, confidences
