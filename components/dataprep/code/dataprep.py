import argparse
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

parser = argparse.ArgumentParser()
parser.add_argument('--price_data',     type=str, required=True)
parser.add_argument('--sentiment_data', type=str, required=True)
parser.add_argument('--mode',           type=str, default='single',
                    help='single = one stock | multi = all stocks')
parser.add_argument('--stock',          type=str, default='AAPL',
                    help='Stock symbol to use in single mode, e.g. AAPL, GOOG, MSFT')
parser.add_argument('--output_data',    type=str, required=True)
args = parser.parse_args()

os.makedirs(args.output_data, exist_ok=True)

df_prices    = pd.read_csv(args.price_data)
df_sentiment = pd.read_csv(args.sentiment_data)
df_prices['Date']    = pd.to_datetime(df_prices['Date'])
df_sentiment['date'] = pd.to_datetime(df_sentiment['date'])
print(f"Price data:    {df_prices.shape}")
print(f"Sentiment:     {df_sentiment.shape}")

df_sentiment = df_sentiment.rename(columns={'date': 'Date', 'symbol': 'Symbol'})
df = df_prices.merge(df_sentiment, on=['Symbol', 'Date'], how='left')
df['lm_score1']    = df['lm_score1'].fillna(0)
df['lm_level']     = df['lm_level'].fillna(0)
df['lm_sentiment'] = df['lm_sentiment'].fillna('neutral')
print(f"Shape after merge: {df.shape}")

df['target'] = (df.groupby('Symbol')['daily_return'].shift(-1) > 0).astype(int)
df = df.dropna(subset=['target'])
df = pd.get_dummies(df, columns=['lm_sentiment'])
print(f"Target: UP={df['target'].mean():.1%}  DOWN={(1-df['target'].mean()):.1%}")
print(f"Shape: {df.shape}")

price_cols     = ['daily_return', 'Volume']
sentiment_cols = ['lm_score1', 'lm_level']
sent_cols      = [c for c in df.columns if c.startswith('lm_sentiment_')]
feature_cols   = price_cols + sentiment_cols + sent_cols
target_col     = 'target'
print(f"Features: {feature_cols}")
print(f"Number of features: {len(feature_cols)}")

if args.mode == 'single':
    stock    = args.stock.upper()
    df_stock = df[df['Symbol'] == stock].sort_values('Date').reset_index(drop=True)
    if len(df_stock) == 0:
        raise ValueError(f"Stock '{stock}' not found in the dataset.")
    train_size = int(len(df_stock) * 0.60)
    val_size   = int(len(df_stock) * 0.20)
    train = df_stock.iloc[:train_size]
    val   = df_stock.iloc[train_size:train_size + val_size]
    test  = df_stock.iloc[train_size + val_size:]

else:
    train_list, val_list, test_list = [], [], []
    for symbol, df_stock in df.groupby('Symbol'):
        df_stock = df_stock.sort_values('Date').reset_index(drop=True)
        train_size = int(len(df_stock) * 0.60)
        val_size   = int(len(df_stock) * 0.20)
        train_list.append(df_stock.iloc[:train_size])
        val_list.append(df_stock.iloc[train_size:train_size + val_size])
        test_list.append(df_stock.iloc[train_size + val_size:])
    train = pd.concat(train_list).reset_index(drop=True)
    val   = pd.concat(val_list).reset_index(drop=True)
    test  = pd.concat(test_list).reset_index(drop=True)

print(f"Train: {len(train)}  Val: {len(val)}  Test: {len(test)}")

scaler  = StandardScaler()
X_train = scaler.fit_transform(train[feature_cols])
X_val   = scaler.transform(val[feature_cols])
X_test  = scaler.transform(test[feature_cols])
y_train = train[target_col].values
y_val   = val[target_col].values
y_test  = test[target_col].values

np.save(os.path.join(args.output_data, 'X_train.npy'), X_train)
np.save(os.path.join(args.output_data, 'X_val.npy'),   X_val)
np.save(os.path.join(args.output_data, 'X_test.npy'),  X_test)
np.save(os.path.join(args.output_data, 'y_train.npy'), y_train)
np.save(os.path.join(args.output_data, 'y_val.npy'),   y_val)
np.save(os.path.join(args.output_data, 'y_test.npy'),  y_test)

with open(os.path.join(args.output_data, 'scaler.pkl'), 'wb') as f:
    pickle.dump(scaler, f)

metadata = {
    'feature_cols': feature_cols,
    'n_features':   len(feature_cols),
    'window_size':  5,
    'mode':         args.mode,
    'stock':        args.stock.upper() if args.mode == 'single' else 'ALL',
}
with open(os.path.join(args.output_data, 'metadata.pkl'), 'wb') as f:
    pickle.dump(metadata, f)

print("Dataprep complete. Saved files:")
for f in os.listdir(args.output_data):
    print(f"  {f}")
