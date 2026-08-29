FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Системные зависимости
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*


# Сначала requirements — чтобы Docker мог кэшировать этот слой
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Исходники Django
COPY . .

# Collect static files (настраивается если нужна django admin panel)
# RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "myblog_backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
