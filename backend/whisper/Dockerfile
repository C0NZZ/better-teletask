FROM python:3.13-trixie

WORKDIR /whisper

COPY checker.py database.py index.py krabbler2.py whisper.py requirements.txt logger.py ./

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

RUN pip install -r requirements.txt

ENV HF_HOME=${HF_HOME:-/models/huggingface} \
    TORCH_HOME=${TORCH_HOME:-/models/torch} \
    LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-/usr/local/lib/python3.13/site-packages/nvidia/cudnn/lib/}

RUN mkdir input output

CMD [ "python", "index.py" ]