from datetime import datetime
import numpy as np
from fastapi import APIRouter, HTTPException
import state
from schemas import PredictRequest

router = APIRouter()


@router.post("/predict")
def predict(req: PredictRequest):
    symbol     = req.symbol.upper()
    model_type = req.model_type.lower()

    if model_type not in ("single", "multi"):
        raise HTTPException(status_code=400, detail="model_type must be 'single' or 'multi'")
    if model_type == "single" and symbol != "AAPL":
        raise HTTPException(status_code=400, detail="Single-stock model only supports AAPL")

    try:
        start = datetime.strptime(req.start_date, "%Y-%m-%d").date()
        end   = datetime.strptime(req.end_date,   "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be YYYY-MM-DD")

    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    feature_cols  = state.get_feature_cols(model_type)
    trading_dates = state.get_trading_dates(symbol, start, end)

    if not trading_dates:
        raise HTTPException(status_code=404, detail=f"No trading data for {symbol} between {start} and {end}")

    # Build a window for each date, skip dates without enough prior history
    all_windows = []
    valid_dates = []
    for dt in trading_dates:
        target_date = dt.date()
        try:
            window = state.get_window(symbol, target_date, model_type)
            all_windows.append(window[feature_cols].values)
            valid_dates.append(target_date)
        except HTTPException:
            continue

    if not all_windows:
        raise HTTPException(status_code=400, detail="No dates with enough prior history to predict")

    # One model call for all dates at once
    X_batch = np.array(all_windows, dtype=float)
    predictions, confidences = state.batch_predict(X_batch, model_type)

    results = []
    for i, target_date in enumerate(valid_dates):
        actual  = state.get_actual(symbol, target_date)
        results.append({
            "date":       target_date.strftime("%Y-%m-%d"),
            "prediction": predictions[i],
            "confidence": confidences[i],
            "actual":     actual,
            "correct":    predictions[i] == actual if actual is not None else None,
        })
    return results
