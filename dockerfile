FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Recolectar archivos estáticos
RUN python manage.py collectstatic --noinput

# Puerto 8080 es el estándar de Cloud Run
EXPOSE 8080

CMD ["gunicorn", "imago.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120"]