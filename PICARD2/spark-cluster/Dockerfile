FROM apache/spark:3.5.8-scala2.12-java17-python3-ubuntu

# Switch to root to install system-wide Python packages
USER root

# Copy requirements and install
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Switch back to the default spark user
USER 185