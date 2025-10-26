FROM python:3.13-trixie

WORKDIR /whisper

COPY checker.py database.py index.py krabbler2.py whisper.py requirements.txt logger.py ./

RUN echo -e 'POSTGRES_DB = "postgres"\nPOSTGRES_USER = "postgres"\nPOSTGRES_PASSWORD = "password"\nDB_HOST = "database"\nDB_PORT = "5432"\nRECORDING_SOURCE_FOLDER = ""\nVTT_DEST_FOLDER = ""' > .env

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

RUN pip install -r requirements.txt

ENV LD_LIBRARY_PATH="/usr/local/lib/python3.13/site-packages/nvidia/cudnn/lib/"

RUN mkdir input output

# COPY cronjob curl auf http://localhost:8000/start-checker

CMD [ "python", "index.py" ]