FROM python:3.11-slim

# wkhtmltopdf (patched-Qt build) — required by services/pdf_generator for headless PDF rendering.
# The distro apt package ships an unpatched Qt that fails without an X server, so install the
# official patched .deb for Debian bookworm (matches the python:3.11-slim base).
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && WK_DEB=wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && curl -sSLo "/tmp/$WK_DEB" \
       "https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/$WK_DEB" \
    && apt-get install -y "/tmp/$WK_DEB" \
    && rm -rf "/tmp/$WK_DEB" /var/lib/apt/lists/* \
    && wkhtmltopdf --version

WORKDIR /app

# Build context is ./backend (see .github/workflows/deploy.yml), so paths are relative to backend/.
COPY requirements.txt .
RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure outputs directory exists
RUN mkdir -p /app/outputs

EXPOSE 8000
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
