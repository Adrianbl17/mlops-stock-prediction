from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import state
from routers import health, stocks, data, predict


@asynccontextmanager
async def lifespan(_: FastAPI):
    state.load_data()
    state.load_models()
    yield


app = FastAPI(title="Stock Prediction API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(stocks.router)
app.include_router(data.router)
app.include_router(predict.router)
