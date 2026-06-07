from datetime import date

import psycopg2

from config import DATABASE_URL


def save_prediction(symbol: str, model_type: str, target_date: date, prediction: str, confidence: float, is_simulation: bool) -> None:
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO predictions (symbol, model_type, date, prediction, confidence, is_simulation)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (symbol, model_type, target_date, prediction, confidence, is_simulation),
            )
        conn.commit()
    finally:
        conn.close()


def get_history(limit: int = 50) -> list[dict]:
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT symbol, model_type, date, prediction, confidence, is_simulation, predicted_at
                FROM predictions
                ORDER BY predicted_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        {
            "symbol":        symbol,
            "model_type":    model_type,
            "date":          target_date.strftime("%Y-%m-%d"),
            "prediction":    prediction,
            "confidence":    confidence,
            "is_simulation": is_simulation,
            "predicted_at":  predicted_at.strftime("%Y-%m-%d %H:%M"),
        }
        for symbol, model_type, target_date, prediction, confidence, is_simulation, predicted_at in rows
    ]
