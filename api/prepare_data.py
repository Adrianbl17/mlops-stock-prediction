"""
Runs automatically during docker build (builder stage).
Reads price_data_clean.csv + sentiment_clean.csv from data/
Saves data/merged.csv with all 7 model features ready to use.
"""

import os
import pandas as pd

DATA_DIR = os.getenv("DATA_DIR", "data")

prices    = pd.read_csv(os.path.join(DATA_DIR, "price_data_clean.csv"))
sentiment = pd.read_csv(os.path.join(DATA_DIR, "sentiment_clean.csv"))

prices["Date"]    = pd.to_datetime(prices["Date"])
sentiment["date"] = pd.to_datetime(sentiment["date"])

sentiment = sentiment.rename(columns={"date": "Date", "symbol": "Symbol"})

df = prices.merge(sentiment, on=["Symbol", "Date"], how="left")

df["lm_score1"]    = df["lm_score1"].fillna(0)
df["lm_level"]     = df["lm_level"].fillna(0)
df["lm_sentiment"] = df["lm_sentiment"].fillna("neutral")

df = pd.get_dummies(df, columns=["lm_sentiment"])

for col in ("lm_sentiment_negative", "lm_sentiment_neutral", "lm_sentiment_positive"):
    if col not in df.columns:
        df[col] = 0.0
    df[col] = df[col].astype(float)

df = df.sort_values(["Symbol", "Date"]).reset_index(drop=True)

out = os.path.join(DATA_DIR, "merged.csv")
df.to_csv(out, index=False)
print(f"Saved {len(df):,} rows to {out}")
