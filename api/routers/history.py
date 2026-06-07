from datetime import datetime

from fastapi import APIRouter, HTTPException

import db
from schemas import SaveHistoryRequest

router = APIRouter()


@router.get("/history")
def list_history():
    return db.get_history()


@router.post("/history")
def save_history(req: SaveHistoryRequest):
    try:
        target_date = datetime.strptime(req.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")

    db.save_prediction(
        symbol=req.symbol.upper(),
        model_type=req.model_type.lower(),
        target_date=target_date,
        prediction=req.prediction,
        confidence=req.confidence,
        is_simulation=req.is_simulation,
    )
    return {"status": "saved"}
