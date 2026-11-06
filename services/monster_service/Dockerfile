FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY services/ ./services/

RUN useradd --create-home appuser

USER appuser

EXPOSE 8002

CMD ["uvicorn", "services.monster_service.main:app", "--host", "0.0.0.0", "--port", "8002"]