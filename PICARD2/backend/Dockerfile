# Use the official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (like Java for Spark if needed)
RUN apt-get update && apt-get install -y default-jre

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Run the server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
