# Use official Python slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy all files into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn pyngrok pytz

# Expose port for Koyeb
EXPOSE 8080

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
