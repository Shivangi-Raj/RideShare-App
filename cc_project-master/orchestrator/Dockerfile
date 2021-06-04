FROM ubuntu:18.04

RUN apt-get update && \
    apt-get install -y python3 && \
    apt-get install -y python3-pip && \
    pip3 install docker --upgrade && \
    pip3 install pika --upgrade && \
    pip3 install flask requests jsonify Response docker kazoo


WORKDIR /api

COPY . /api

EXPOSE 3002

CMD python3 orchestrator.py

