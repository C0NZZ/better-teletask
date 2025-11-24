FROM python:3.11-trixie

WORKDIR /whisper

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    pkg-config \
    build-essential \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev

COPY requirements.txt ./

RUN pip install -r requirements.txt

RUN pip install \
    torch==2.4.0+cu124 \
    torchaudio==2.4.0+cu124 \
    --index-url https://download.pytorch.org/whl/cu124

COPY crawlnewids.py database.py index.py krabbler.py logger.py whisper.py ./

ENV HF_HOME=${HF_HOME:-/models/huggingface} \
    TORCH_HOME=${TORCH_HOME:-/models/torch} \
    LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-/usr/local/lib/python3.11/site-packages/nvidia/cudnn/lib/}

RUN mkdir input output

CMD [ "python", "index.py" ]