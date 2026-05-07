FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install system-wide Python packages
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy our simple HTTP executor service
COPY server.py /app/server.py

EXPOSE 8080