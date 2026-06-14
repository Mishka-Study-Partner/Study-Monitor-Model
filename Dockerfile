# Dockerfile (Study Monitor Model)
# Stage 1: مرحلة البناء وتحميل المكتبات الثقيلة
FROM python:3.10-slim AS builder

WORKDIR /app

# تثبيت حزم النظام الأساسية لـ MediaPipe و OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

ENV PIP_DEFAULT_TIMEOUT=3000
ENV PIP_NO_CACHE_DIR=1

COPY requirements.txt .

# تحديث pip وتثبيت الـ Requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --retries 10 -r requirements.txt

# Stage 2: النسخة النهائية الخفيفة والمستقرة
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# نقل المكتبات الجاهزة من الـ builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

# بورت افتراضي للموديل الثاني لتجنب التعارض مع الموديل الأول
EXPOSE 5001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
