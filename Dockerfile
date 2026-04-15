# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirement files first for better caching
COPY core/requirements.txt ./core/

# Install the Python dependencies (Upgrade pip first)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r core/requirements.txt

# Copy the entire backend source code
COPY core/ ./core/

# Set the Environment variables 
ENV PYTHONPATH="/app/core/src"
ENV ECHO_DB_PATH="/data/echo_app.db"

# Expose the API port (7860 is required for completely free Hugging Face Spaces)
EXPOSE 7860

# Start Uvicorn pointing to the main app inside core/src/pipeline/api/main.py
CMD ["sh", "-c", "uvicorn pipeline.api.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
