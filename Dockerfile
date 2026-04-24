# Use slim Python image
FROM python:3.11-slim

# Prevent Python from buffering logs
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app_v1

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY ../app_v1/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r ../app_v1/requirements.txt

# Copy your code
COPY . .

# Expose port (Render expects 10000 usually)
EXPOSE 10000

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]