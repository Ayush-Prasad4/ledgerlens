FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV FASTEMBED_CACHE_PATH=/models
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')"

COPY ledgerlens ./ledgerlens

EXPOSE 8000
CMD ["uvicorn", "ledgerlens.api:app", "--host", "0.0.0.0", "--port", "8000"]
