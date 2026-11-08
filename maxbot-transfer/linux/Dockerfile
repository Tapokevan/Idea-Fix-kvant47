FROM python:3.11-slim@sha256:b701198cb708b68d9413ca67d6311bd97c9389a2c5fe4da0511fc652642366cd

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/vendor \
    MAX_DB_PATH=/data/school_bot.db

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --target /app/vendor -r requirements.txt

COPY maxbot ./maxbot

RUN mkdir -p /data
VOLUME ["/data"]

CMD ["python", "-m", "maxbot"]
