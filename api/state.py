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
