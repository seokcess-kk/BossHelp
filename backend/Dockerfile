FROM python:3.12-slim

WORKDIR /app

# Install dependencies (빌드 컨텍스트가 루트이므로 backend/ 경로 사용)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ .

# Expose port (Railway sets PORT dynamically)
EXPOSE 8000

# Run the application with dynamic port
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
