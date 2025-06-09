# Use an official lightweight Python image.
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY ./crow_eye_api /app/crow_eye_api
COPY ./data /app/data

# The command to run the application
# We use gunicorn for production instead of uvicorn's development server
# The number of workers is a recommendation, can be tuned.
# Gunicorn will bind to the port specified by the PORT environment variable.
CMD exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind "0.0.0.0:${PORT}" crow_eye_api.main:app 