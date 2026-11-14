FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

RUN useradd -u 1000 -m appuser
USER appuser

# Il codice e il database restano montati da host in /app
WORKDIR /app
CMD ["python", "script.py"]
