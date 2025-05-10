FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Matplotlib and PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev \
    python3-dev \
    libfreetype6-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY project_requirements.txt .
RUN pip install --no-cache-dir -r project_requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p logs output person_lists

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]