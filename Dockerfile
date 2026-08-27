FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --retries 10 --timeout 120 -r requirements.txt

COPY . .

COPY .docker.env .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]