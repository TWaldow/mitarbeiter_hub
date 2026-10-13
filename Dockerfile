# 1. Basis-Image
FROM python:3.12.7-slim

# 2. Arbeitsverzeichnis im Container
WORKDIR /app

# 3. Dependencies kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Restlichen Projektcode kopieren
COPY . .

# 5. Interner Port für Flask
EXPOSE 5000

# 6. Startbefehl (Modul app.py, Flask-Objekt app)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
