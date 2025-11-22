FROM python:3.13-trixie

WORKDIR /whisper

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY crawlnewids.py database.py index.py krabbler.py logger.py whisper.py ./

ENV HF_HOME=${HF_HOME:-/models/huggingface} \
    TORCH_HOME=${TORCH_HOME:-/models/torch} \
    LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-/usr/local/lib/python3.13/site-packages/nvidia/cudnn/lib/}

RUN mkdir input output

CMD [ "python", "index.py" ]