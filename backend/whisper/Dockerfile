FROM python:3.12-slim-trixie

WORKDIR /whisper

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir \
    torch==2.4.0+cu124 \
    torchaudio==2.4.0+cu124 \
    --index-url https://download.pytorch.org/whl/cu124

COPY crawlnewids.py database.py index.py krabbler.py logger.py whisper.py chain.pem utils ./

ENV HF_HOME=${HF_HOME:-/models/huggingface} \
    TORCH_HOME=${TORCH_HOME:-/models/torch} \
    LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-/usr/local/lib/python3.12/site-packages/nvidia/cudnn/lib/}

RUN mkdir input output

CMD [ "python", "index.py" ]