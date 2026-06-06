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
        target_date = datetime.strptime(req.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")

    feature_cols = state.get_feature_cols(model_type)
    window_size  = state.metadatas[model_type]["window_size"]
    n_features   = len(feature_cols)

    if len(req.features) != window_size or any(len(row) != n_features for row in req.features):
        raise HTTPException(
            status_code=400,
            detail=f"features must be {window_size}x{n_features} (got {len(req.features)}x{len(req.features[0]) if req.features else 0})"
        )

    # Baseline: real values from the dataset
    real_window = state.get_window(symbol, target_date, model_type)
    X_real      = real_window[feature_cols].values
    baseline_pred, baseline_conf, baseline_prob = state.run_prediction(X_real, model_type)

    # Simulated: user-modified values
    X_sim = np.array(req.features, dtype=float)
    sim_pred, sim_conf, sim_prob = state.run_prediction(X_sim, model_type)

    # TODO: log simulated prediction to DB with is_simulation=True (after DB is set up)

    return {
        "baseline_prediction":  baseline_pred,
        "baseline_confidence":  baseline_conf,
        "simulated_prediction": sim_pred,
        "simulated_confidence": sim_conf,
        "delta":                round(sim_prob - baseline_prob, 4),
        "feature_cols":         feature_cols,
    }
