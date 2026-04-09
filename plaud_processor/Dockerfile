FROM python:3.12-slim

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /app

# Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode
COPY . .

# Daten-Verzeichnis
RUN mkdir -p /data/uploads /data/output

# Port für Web-UI
EXPOSE 8080

# Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/data
