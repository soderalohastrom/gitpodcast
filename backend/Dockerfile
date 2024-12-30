# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    libasound2 \
    libasound2-dev \
    wget \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*


# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create and set permissions for entrypoint script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh && \
    # Ensure the script uses Unix line endings
    sed -i 's/\r$//' /app/entrypoint.sh && \
    # Double check permissions
    ls -la /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Use entrypoint script
CMD ["/bin/bash", "/app/entrypoint.sh"]
