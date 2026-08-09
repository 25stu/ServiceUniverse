FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY services/water_billing/requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/requirements.txt

COPY services/water_billing /app/services/water_billing

CMD ["uvicorn", "services.water_billing.app.main:app", "--host", "0.0.0.0", "--port", "8101"]
