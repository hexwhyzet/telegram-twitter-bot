# syntax=docker/dockerfile:1

FROM python:3.10.7-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY ../telegram-twitter-bot%20copy .

CMD [ "python3", "main.py" ]