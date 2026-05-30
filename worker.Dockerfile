FROM python:3.11-bullseye
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y wget gnupg ca-certificates curl unzip fonts-liberation libnss3 libatk1.0-0 libatk-bridge2.0-0 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 libwayland-client0 libwayland-egl1 libdbus-1-3 libgtk-3-0 libxss1 && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN python -m playwright install --with-deps

COPY backend /app/backend
WORKDIR /app/backend

CMD ["celery", "-A", "app.celery_app.app", "worker", "--loglevel=info", "-Q", "monitoring,screenshots,ai,notifications"]
