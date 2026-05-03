FROM python:3.11-slim

# Prevent interactive install
ENV DEBIAN_FRONTEND=noninteractive

# System deps for OpenCV, EasyOCR, and image processing
# Added build-essential and python3-dev for potential compilation needs
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgl1-mesa-glx \
    wget \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install deps — no-cache keeps image small
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download EasyOCR models (optional, kept for compatibility)
# RUN python3 -c "import easyocr; reader = easyocr.Reader(['en', 'hi'], gpu=False)"

# Copy the rest of the application code
COPY . .

# Use Render's $PORT environment variable, defaulting to 10000
ENV PORT=10000
EXPOSE 10000

# Streamlit configuration
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=10000 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Run streamlit, using the PORT env var
CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.headless=true", \
     "--server.port=10000", \
     "--server.address=0.0.0.0"]
