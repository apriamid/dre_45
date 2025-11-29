# Builder Stage
FROM python:3.12-slim-bullseye As builder

# Instal dependensi build dalam satu langkah dan bersihkan cache
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Buat virtual env
RUN python -m venv /opt/venv

# Set PATH untuk menggunakan biner dari venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------------------------------------------------
# Operational Stage
# ----------------------------------------------------------------------
FROM python:3.12-slim-bullseye

# Instal library runtime yang diperlukan (misalnya libpq5) dan bersihkan cache
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Dapatkan virtual env dari builder stage
COPY --from=builder /opt/venv /opt/venv

# Set PATH dan variabel lingkungan lainnya
ENV PATH="/opt/venv/bin:$PATH"
ENV CLOUD_APPS CLOUD_RUN
ENV PORT 8080 # Set default PORT, tapi Cloud Run akan menimpanya

WORKDIR /pythonproject
COPY . ./

# Perintah menjalankan Gunicorn yang sudah dioptimalkan:
# Menggunakan variabel $PORT yang disuntikkan oleh Cloud Run
CMD ["gunicorn", "--worker-class", "eventlet", "--bind", "0.0.0.0:$PORT", "--workers", "1", "-t", "4", "app:app"]