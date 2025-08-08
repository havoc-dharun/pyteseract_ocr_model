# ---- Build frontend ----
FROM node:22-alpine AS frontend
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --silent
COPY ./src ./src
COPY ./index.html ./
COPY ./vite.config.js ./
RUN npm run build

# ---- Backend runtime ----
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

# System deps: Tesseract and libraries for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr libtesseract-dev libleptonica-dev libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Copy built frontend to /app/dist
COPY --from=frontend /app/dist ./dist

EXPOSE 8000
CMD ["python", "server.py"]