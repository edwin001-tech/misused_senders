# Base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Set time zone
ENV TZ=Africa/Nairobi
RUN apt-get update && apt-get install -y tzdata && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    cron \
    && apt-get clean

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the model
RUN python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='valhalla/distilbart-mnli-12-9')"

# Copy application files
COPY . .

#RUN echo "* * * * * /usr/local/bin/python /app/run_daily.py >> /app/daily_task.log 2>&1" > /etc/cron.d/my-cron

#make script to be executable
RUN chmod 755 /app/run_daily.py

# Start cron and keep the container running
CMD ["cron", "-f"]
