# Stage 1: Build stage
FROM python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download and install FFmpeg from static build
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
    && tar xvf ffmpeg-release-amd64-static.tar.xz \
    && mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ \
    && mv ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ \
    && chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe \
    && rm -rf ffmpeg-*-amd64-static*

# Stage 2: Runtime stage
FROM python:3.9-slim

# Copy FFmpeg binaries from builder stage
COPY --from=builder /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg
COPY --from=builder /usr/local/bin/ffprobe /usr/local/bin/ffprobe

# Make FFmpeg executable
RUN chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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

# Verify FFmpeg installation
RUN ffmpeg -version && ffprobe -version

# Expose port
EXPOSE 8000

# Command to run the application
CMD uvicorn web:app --host 0.0.0.0 --port ${PORT:-8000}
