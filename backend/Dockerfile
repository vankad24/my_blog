FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Системные зависимости
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gnupg \
    && install -d /usr/share/postgresql-common/pgdg \
    && curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
        --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] http://apt.postgresql.org/pub/repos/apt trixie-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential libpq-dev postgresql-client-18 \
    && rm -rf /var/lib/apt/lists/*


# Сначала requirements — чтобы Docker мог кэшировать этот слой
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Исходники Django
COPY . .

# Collect static files (настраивается если нужна django admin panel)
# RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Запускаем миграции перед gunicorn
CMD python manage.py migrate --noinput && gunicorn myblog_backend.wsgi:application --bind 0.0.0.0:8000 --workers 3
