import os
from typing import Optional
import pandas as pd
from config import DATA_DIR

df: Optional[pd.DataFrame] = None


def load_data():
    global df
    path = os.path.join(DATA_DIR, "merged.csv")
    df   = pd.read_csv(path, parse_dates=["Date"])
    print(f"[startup] Data loaded: {len(df):,} rows, {df['Symbol'].nunique()} symbols")


def get_symbols() -> list:
    assert df is not None, "Data not loaded - call load_data() first"
    return sorted(df["Symbol"].unique().tolist())
