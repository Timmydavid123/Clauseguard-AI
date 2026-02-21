FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    zstd \
    gcc \
    libmagic1 \
    libglib2.0-0 \
    libgl1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN curl -fsSL https://ollama.com/install.sh | sh


ENV OLLAMA_MODEL=qwen2.5:3b-instruct
ENV OLLAMA_URL=http://127.0.0.1:11434/api/chat

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]