from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
import state

router = APIRouter()


@router.get("/data")
def get_data(symbol: str = Query(...), date: str = Query(...)):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")

    sym          = symbol.upper()
    feature_cols = state.get_feature_cols("single")
    window       = state.get_window(sym, target_date, "single")

    return {
        "symbol":       sym,
        "target_date":  date,
        "feature_cols": feature_cols,
        "window": [
            {
                "date":   row["Date"].strftime("%Y-%m-%d"),
                "values": [float(row[col]) for col in feature_cols],
            }
            for _, row in window.iterrows()
        ],
    }
