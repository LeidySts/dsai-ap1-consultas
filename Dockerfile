# 1) build do frontend
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY src/frontend/package.json src/frontend/package-lock.json ./
RUN npm ci
COPY src/frontend/ ./
RUN npm run build

# 2) API + estáticos
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY src/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/ ./
COPY --from=frontend /frontend/dist ./app/static
EXPOSE 8000
CMD ["sh", "start.sh"]
