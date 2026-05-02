FROM python:3.11-slim

# Minimal system dependencies for Tectonic
RUN apt-get update && apt-get install -y \
    tectonic \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Ensure outputs directory exists
RUN mkdir -p /app/outputs

EXPOSE 8000
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"