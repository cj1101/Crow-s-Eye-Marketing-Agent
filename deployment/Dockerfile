# Crow's Eye Marketing Platform - Docker Configuration
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ../src ./src
COPY ../assets ./assets
COPY ../translations ./translations
COPY ../main.py .

# Create data directories
RUN mkdir -p data/templates data/samples

# Set environment variables
ENV PYTHONPATH=/app/src
ENV QT_QPA_PLATFORM=xcb

# Expose port for OAuth callback server
EXPOSE 8080

# Run the application
CMD ["python", "main.py"] 