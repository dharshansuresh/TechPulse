FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure storage directories exist
RUN mkdir -p storage/uploads storage/chroma_db storage/logs

# Expose ports: FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Default command launches both services
CMD ["python", "app.py", "--mode", "all"]
