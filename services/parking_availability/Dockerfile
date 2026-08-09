FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY services/parking_availability/requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/requirements.txt

COPY services/__init__.py /app/services/__init__.py
COPY services/parking_availability /app/services/parking_availability

EXPOSE 8301

CMD ["uvicorn", "services.parking_availability.app.main:app", "--host", "0.0.0.0", "--port", "8301"]
