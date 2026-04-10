FROM python:3.12-slim

# ffmpeg für Whisper-Audioverarbeitung
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Abhängigkeiten zuerst (besseres Layer-Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungs-Code
COPY . .

# Daten-Ordner anlegen
RUN mkdir -p /data/output /data/uploads /data/incoming

EXPOSE 8080

# Standard-Befehl für den Prozessor-Container
CMD ["python", "main.py"]
