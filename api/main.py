from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import state
from routers import health, stocks


@asynccontextmanager
async def lifespan(_: FastAPI):
    state.load_data()
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
