from datetime import datetime
import numpy as np
from fastapi import APIRouter, HTTPException
import state
from schemas import SimulateRequest

router = APIRouter()


@router.post("/simulate")
def simulate(req: SimulateRequest):
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

    all_windows, valid_dates = [], []
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

    X_batch = np.array(all_windows, dtype=float)
    predictions, confidences = state.batch_predict(X_batch, model_type)

    capital  = req.initial_capital
    baseline = req.initial_capital
    correct  = 0
    daily    = []

    for i, target_date in enumerate(valid_dates):
        actual       = state.get_actual(symbol, target_date)
        daily_return = state.get_daily_return(symbol, target_date)

        is_correct = predictions[i] == actual if actual is not None else None
        if is_correct:
            correct += 1

        # Model strategy: invest on UP prediction, stay cash on DOWN
        if predictions[i] == "UP" and daily_return is not None:
            capital *= (1 + daily_return)

        # Baseline: always invested (buy and hold)
        if daily_return is not None:
            baseline *= (1 + daily_return)

        daily.append({
            "date":            target_date.strftime("%Y-%m-%d"),
            "prediction":      predictions[i],
            "actual":          actual,
            "correct":         is_correct,
            "portfolio_value": round(capital, 2),
            "baseline_value":  round(baseline, 2),
        })

    total    = len(valid_dates)
    accuracy = round(correct / total, 4) if total > 0 else 0

    return {
        "summary": {
            "symbol":               symbol,
            "model_type":           model_type,
            "initial_capital":      req.initial_capital,
            "final_portfolio":      round(capital, 2),
            "final_baseline":       round(baseline, 2),
            "total_return_pct":     round((capital  - req.initial_capital) / req.initial_capital * 100, 2),
            "baseline_return_pct":  round((baseline - req.initial_capital) / req.initial_capital * 100, 2),
            "total_days":           total,
            "correct":              correct,
            "accuracy":             accuracy,
        },
        "daily": daily,
    }
