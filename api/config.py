import os

MODELS_DIR = os.getenv("MODELS_DIR", "models")
DATA_DIR   = os.getenv("DATA_DIR",   "data")

DATABASE_URL = os.getenv("DATABASE_URL") or (
    f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'postgres')}"
    f"@{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB', 'predictions')}"
)
