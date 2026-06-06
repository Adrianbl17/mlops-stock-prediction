import os

MODELS_DIR   = os.getenv("MODELS_DIR",   "models")
DATA_DIR     = os.getenv("DATA_DIR",     "data")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/predictions")
