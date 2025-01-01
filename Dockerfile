# Use jrottenberg/ffmpeg as base image
FROM jrottenberg/ffmpeg:4.4-ubuntu AS ffmpeg

# Use Python slim image for final build
FROM python:3.9-slim

# Copy FFmpeg from the ffmpeg image
COPY --from=ffmpeg /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg /usr/local/bin/ffprobe /usr/local/bin/ffprobe

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libssl1.1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && chmod +x /usr/local/bin/ffmpeg \
    && chmod +x /usr/local/bin/ffprobe \
    && ln -s /usr/local/bin/ffmpeg /usr/bin/ffmpeg \
    && ln -s /usr/local/bin/ffprobe /usr/bin/ffprobe

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploaded_files && chmod 777 uploaded_files

# Set environment variables
ENV PATH="/usr/local/bin:${PATH}"
ENV FFMPEG_PATH="/usr/local/bin/ffmpeg"
ENV FFPROBE_PATH="/usr/local/bin/ffprobe"

# Verify FFmpeg installation and permissions
RUN ls -l /usr/local/bin/ffmpeg /usr/bin/ffmpeg && \
    ls -l /usr/local/bin/ffprobe /usr/bin/ffprobe && \
    echo "FFmpeg version:" && ffmpeg -version && \
    echo "FFmpeg location:" && which ffmpeg && \
    echo "FFmpeg permissions:" && ls -l $(which ffmpeg)

# Expose port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "web:app", "--host", "0.0.0.0", "--port", "8000"]
