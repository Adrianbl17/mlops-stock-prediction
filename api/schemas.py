from pydantic import BaseModel


class PredictRequest(BaseModel):
    symbol: str
    model_type: str
    start_date: str
    end_date: str


class SimulateRequest(BaseModel):
    symbol: str
    model_type: str
    start_date: str
    end_date: str
    initial_capital: float = 1000.0
