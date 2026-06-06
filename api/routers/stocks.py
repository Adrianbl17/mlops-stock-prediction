from fastapi import APIRouter, HTTPException, Query
import state

router = APIRouter()


@router.get("/stocks")
def get_stocks(model_type: str = Query("multi")):
    mt = model_type.lower()
    if mt not in ("single", "multi"):
        raise HTTPException(status_code=400, detail="model_type must be 'single' or 'multi'")
    if mt == "single":
        return {"model_type": "single", "symbols": ["AAPL"]}
    return {"model_type": "multi", "symbols": state.get_symbols()}
