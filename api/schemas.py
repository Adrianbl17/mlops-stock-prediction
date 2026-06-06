from pydantic import BaseModel


class PredictRequest(BaseModel):
    symbol: str
    model_type: str
    start_date: str
    end_date: str
