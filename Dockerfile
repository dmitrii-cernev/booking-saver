# Dockerfile
FROM python:3.10-slim

# Install Chromium & Chromedriver dependencies
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    wget \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Tell Selenium where to find Chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Default entrypoint
ENTRYPOINT ["./entrypoint.sh"]
