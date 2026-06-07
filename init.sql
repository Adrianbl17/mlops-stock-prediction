CREATE TABLE IF NOT EXISTS predictions (
    id            SERIAL PRIMARY KEY,
    symbol        VARCHAR(10),
    model_type    VARCHAR(10),
    date          DATE,
    prediction    VARCHAR(4),
    confidence    FLOAT,
    is_simulation BOOLEAN DEFAULT FALSE,
    predicted_at  TIMESTAMP DEFAULT NOW()
);