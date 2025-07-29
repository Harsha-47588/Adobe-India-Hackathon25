FROM --platform=linux/amd64 python:3.10-slim

# Set working directory
WORKDIR /app

# Copy necessary files
COPY main.py .
COPY requirements.txt .
COPY schema ./schema

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create input/output directories
RUN mkdir -p /app/input /app/output

# Run the main script
CMD ["python", "main.py"]