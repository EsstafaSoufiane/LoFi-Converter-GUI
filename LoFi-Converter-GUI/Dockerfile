# Use Python slim image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploaded_files && chmod 777 uploaded_files

# Verify FFmpeg installation
RUN ffmpeg -version

# Expose port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "web:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
