FROM python:3.11-slim

# Install system dependencies including deno for yt-dlp JavaScript extraction
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install deno for YouTube JavaScript runtime
RUN curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh
ENV PATH="/usr/local/bin:$PATH"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Whisper tiny model during build to avoid OOM at runtime
# This bundles the model into the Docker image so it loads instantly
RUN python -c "
from faster_whisper import WhisperModel
print('Pre-downloading Whisper tiny model...')
model = WhisperModel('tiny', device='cpu', compute_type='int8')
print('Model downloaded and cached successfully')
"

COPY . .

RUN mkdir -p /tmp/youtube-clipper/output /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]