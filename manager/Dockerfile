FROM python:3-alpine

WORKDIR /app

RUN apk update && apk add git

COPY requirements.txt /app
COPY manager.py /app

RUN pip3 install -r /app/requirements.txt

CMD ["python3", "/app/manager.py"]