# Builder
FROM python:3.10-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime
FROM python:3.10-slim
WORKDIR /app

COPY --from=builder /root/.local /app/.local
ENV PATH=/app/.local/bin:$PATH
ENV PYTHONPATH=/app/.local/lib/python3.10/site-packages:$PYTHONPATH

RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

COPY --chown=appuser:appuser . .

USER appuser

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]