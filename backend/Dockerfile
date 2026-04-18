FROM python:3.11-slim

# System dependencies for Tectonic
RUN apt-get update && apt-get install -y \
    curl \
    libssl-dev \
    libfontconfig1 \
    libgraphite2-dev \
    libharfbuzz-dev \
    libicu-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Tectonic binary (latest stable)
RUN curl -fsSL \
  https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic@0.14.1/tectonic-0.14.1-x86_64-unknown-linux-musl.tar.gz \
  | tar xz -C /usr/local/bin/

# Pre-warm Tectonic with a document that uses all packages from our template so they are cached at BUILD TIME not runtime.
# Copy the warmup tex file (which uses: charter, fontawesome5, paracol, eso-pic, titlesec, enumitem, changepage, needspace)
COPY backend/templates/warmup.tex /warmup/warmup.tex
RUN tectonic /warmup/warmup.tex || true && rm -rf /warmup

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]