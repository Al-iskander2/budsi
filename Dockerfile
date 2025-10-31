FROM python:3.12-slim
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-eng tesseract-ocr-spa \
    poppler-utils libgl1 \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV TESSERACT_CMD=/usr/bin/tesseract

RUN python manage.py collectstatic --noinput
RUN mkdir -p /app/media
EXPOSE 10000

CMD ["gunicorn", "budsi_django.wsgi:application", "-b", "0.0.0.0:10000", "-w", "2"]
