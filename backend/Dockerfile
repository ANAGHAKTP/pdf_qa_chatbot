FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

COPY . .

ENV DATABASE_URL="postgresql://postgres.nhrtebrshgutjkydwcim:Anaghaktp%232004@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
ENV USE_S3="False"

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
