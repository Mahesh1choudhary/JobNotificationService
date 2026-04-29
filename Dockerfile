# Use slim Python image
FROM python:3.11-slim

# Prevent Python from buffering logs
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY app_v1/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

# Copy your code
COPY app_v1 ./app_v1

# Expose port (Render expects 10000 usually)
EXPOSE 10000

# Run the app
CMD ["uvicorn", "app_v1.main:app", "--host", "0.0.0.0", "--port", "10000"]