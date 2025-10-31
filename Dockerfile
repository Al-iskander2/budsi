FROM python:3.12-slim
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema necesarias
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      libfreetype6-dev \
      libjpeg-dev \
      zlib1g-dev \
      tesseract-ocr \
      tesseract-ocr-eng \
      tesseract-ocr-spa \
      poppler-utils \
      libgl1 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./

# SOLUCIÓN: Instalar setuptools primero con una versión específica y luego numpy
RUN pip install --upgrade pip
RUN pip install setuptools==69.0.0
RUN pip install wheel

# Instalar numpy primero con una versión compatible
RUN pip install numpy==1.26.0

# Luego instalar el resto de requirements
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TESSERACT_CMD=/usr/bin/tesseract

RUN python manage.py collectstatic --noinput

RUN mkdir -p /app/media

EXPOSE 10000

CMD ["gunicorn", "budsi_django.wsgi:application", "-b", "0.0.0.0:10000", "-w", "2"]