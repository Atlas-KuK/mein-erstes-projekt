# ── Plaud Processor Docker Image ──────────────────────────────────────────────
FROM python:3.12-slim

# ffmpeg für Aufnahmen > 25 MB (Segmentierung)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Abhängigkeiten zuerst (Layer-Cache nutzen)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode
COPY *.py .

# Arbeitsverzeichnis für Logs, PDFs, Statusdateien
VOLUME ["/data"]
ENV WORK_DIR=/data

CMD ["python", "main.py", "--loop"]
