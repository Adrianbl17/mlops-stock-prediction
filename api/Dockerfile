FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir pandas

COPY data/ ./data/
COPY prepare_data.py .
RUN python prepare_data.py

FROM python:3.11-slim AS production

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY config.py .
COPY state.py .
COPY routers/ ./routers/
COPY models/  ./models/

COPY --from=builder /app/data/merged.csv ./data/merged.csv

RUN addgroup --system api && adduser --system --ingroup api api
USER api

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]