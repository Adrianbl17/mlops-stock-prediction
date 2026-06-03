import argparse
import os
import pickle
import numpy as np
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report
from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator
from tensorflow.keras.callbacks import EarlyStopping
from utils import get_dropout, predict_and_score

parser = argparse.ArgumentParser()
parser.add_argument('--input_data',   type=str, required=True)
parser.add_argument('--output_model', type=str, required=True)
args = parser.parse_args()

os.makedirs(args.output_model, exist_ok=True)

X_train = np.load(os.path.join(args.input_data, 'X_train.npy'))
X_val   = np.load(os.path.join(args.input_data, 'X_val.npy'))
X_test  = np.load(os.path.join(args.input_data, 'X_test.npy'))
y_train = np.load(os.path.join(args.input_data, 'y_train.npy'))
y_val   = np.load(os.path.join(args.input_data, 'y_val.npy'))
y_test  = np.load(os.path.join(args.input_data, 'y_test.npy'))

with open(os.path.join(args.input_data, 'scaler.pkl'), 'rb') as f:
    scaler = pickle.load(f)

with open(os.path.join(args.input_data, 'metadata.pkl'), 'rb') as f:
    metadata = pickle.load(f)

window_size = metadata['window_size']
n_features  = metadata['n_features']
print(f"Mode: {metadata['mode']}  |  window_size: {window_size}  |  n_features: {n_features}")

train_gen = TimeseriesGenerator(X_train, y_train, length=window_size, batch_size=32)
val_gen   = TimeseriesGenerator(X_val,   y_val,   length=window_size, batch_size=32)
test_gen  = TimeseriesGenerator(X_test,  y_test,  length=window_size, batch_size=32)
weights      = compute_class_weight('balanced', classes=np.array([0, 1]), y=y_train)
class_weight = {0: weights[0], 1: weights[1]}
print(f"Class weights: {class_weight}")

es         = EarlyStopping(patience=10, restore_best_weights=True)
model_drop = get_dropout(window_size, n_features)
fit_drop   = model_drop.fit(
    train_gen,
    validation_data=val_gen,
    epochs=100,
    class_weight=class_weight,
    callbacks=[es],
    verbose=1
)

best_model = model_drop

acc_train, _, _         = predict_and_score(best_model, train_gen)
acc_val,   _, _         = predict_and_score(best_model, val_gen)
acc_test,  pred, true_y = predict_and_score(best_model, test_gen)

print(f"\nAccuracy Train: {acc_train:.4f}")
print(f"Accuracy Val:   {acc_val:.4f}")
print(f"Accuracy Test:  {acc_test:.4f}")
print()
print(classification_report(true_y, pred))

with open(os.path.join(args.output_model, 'best_model.pkl'), 'wb') as f:
    pickle.dump(best_model, f)

with open(os.path.join(args.output_model, 'scaler.pkl'), 'wb') as f:
    pickle.dump(scaler, f)

with open(os.path.join(args.output_model, 'metadata.pkl'), 'wb') as f:
    pickle.dump(metadata, f)

print("\nTraining complete. Saved files:")
for file in os.listdir(args.output_model):
    print(f"  {file}")
