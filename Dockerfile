FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# IndicTrans2 pre/post-processing (needs cython + numpy at build time)
RUN pip install --no-cache-dir cython numpy && \
    pip install --no-cache-dir git+https://github.com/VarunGumma/IndicTransToolkit.git

COPY . .
