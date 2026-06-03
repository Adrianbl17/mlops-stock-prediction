import numpy as np
from sklearn.metrics import accuracy_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, LSTM, Dense, Dropout

def get_dropout(window_size, n_features):
    model = Sequential([
        Input(shape=(window_size, n_features)),
        LSTM(50, activation='relu', return_sequences=True),
        Dropout(0.2),
        LSTM(50, activation='relu'),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ])
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model

def predict_and_score(model, gen):
    pred_proba = model.predict(gen, verbose=0)
    pred       = (pred_proba > 0.5).astype(int).flatten()
    true_y     = np.concatenate([gen[i][1] for i in range(len(gen))])
    acc        = accuracy_score(true_y, pred)
    return acc, pred, true_y
