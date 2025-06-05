FROM python:3.9-slim 

WORKDIR /app

COPY requirements.txt . 
RUN pip install -r requirements.txt 

COPY . . 

# Expose port for documentation (Cloud Run will override this)
EXPOSE 8000

# Use shell form to allow environment variable expansion
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} 
