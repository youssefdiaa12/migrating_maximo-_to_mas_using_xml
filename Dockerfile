FROM python:3-slim

# Install coreutils (includes sleep)
RUN apt-get update && apt-get install -y coreutils && rm -rf /var/lib/apt/lists/*

# Your existing Dockerfile instructions
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN python -m pip install -r requirements.txt
WORKDIR /app
COPY . /app
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Use sleep infinity
CMD ["sleep", "infinity"]