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

RUN pip install --upgrade pip
RUN pip install setuptools==69.0.0
RUN pip install wheel
RUN pip install numpy==1.26.0
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TESSERACT_CMD=/usr/bin/tesseract

RUN mkdir -p /app/media

EXPOSE 10000

# CREAR SCRIPT DE INICIO que ejecute collectstatic primero
RUN echo '#!/bin/bash\npython manage.py collectstatic --noinput\nexec gunicorn budsi_django.wsgi:application -b 0.0.0.0:10000 -w 2' > /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]