FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set environment variable for FFmpeg
ENV PATH="/usr/bin:${PATH}"
ENV FFMPEG_BINARY="/usr/bin/ffmpeg"
ENV FFPROBE_BINARY="/usr/bin/ffprobe"

# Verify FFmpeg installation and paths
RUN which ffmpeg && \
    which ffprobe && \
    ffmpeg -version && \
    ffprobe -version && \
    ls -l /usr/bin/ffmpeg && \
    ls -l /usr/bin/ffprobe

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads directory with proper permissions
RUN mkdir -p uploaded_files && chmod 777 uploaded_files

# Expose port
EXPOSE 8000

# Command to run the application
CMD uvicorn web:app --host 0.0.0.0 --port ${PORT:-8000}
