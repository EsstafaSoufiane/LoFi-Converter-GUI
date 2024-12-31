# Use Python slim image
FROM python:3.9-slim

# Install system dependencies and FFmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    wget \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Download and install static FFmpeg build (more reliable)
RUN wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar xf ffmpeg-release-amd64-static.tar.xz && \
    mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ && \
    mv ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ && \
    chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe && \
    rm -rf ffmpeg-*-amd64-static* && \
    ln -sf /usr/local/bin/ffmpeg /usr/bin/ffmpeg && \
    ln -sf /usr/local/bin/ffprobe /usr/bin/ffprobe

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

# Set environment variables
ENV PATH="/usr/local/bin:${PATH}"
ENV FFMPEG_PATH="/usr/local/bin/ffmpeg"
ENV FFPROBE_PATH="/usr/local/bin/ffprobe"

# Expose port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "web:app", "--host", "0.0.0.0", "--port", "8000"]
