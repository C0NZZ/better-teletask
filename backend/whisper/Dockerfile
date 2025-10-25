FROM python:3.14-alpine

WORKDIR /whisper

COPY checker.py database.py index.py krabbler2.py whisper.py requirements.txt ./

RUN pip install -r requirements.txt

RUN mkdir input output

# COPY cronjob curl auf http://localhost:8000/start-checker

CMD [ "python index.py" ]