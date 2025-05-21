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

# Create non-root user for security
RUN useradd -m medicalspy

# Create required directories and set permissions
RUN mkdir -p logs output person_lists instance \
    && chown -R medicalspy:medicalspy logs output person_lists instance

# Copy application code
COPY --chown=medicalspy:medicalspy . .

# Rename app.py to avoid confusion
RUN if [ -f backend/app_new.py ]; then mv backend/app_new.py backend/app.py; fi

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    DATABASE_URL=sqlite:///instance/medicalspy.db

# Switch to non-root user
USER medicalspy

# Initialize database if using SQLite
RUN python init_db.py

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]