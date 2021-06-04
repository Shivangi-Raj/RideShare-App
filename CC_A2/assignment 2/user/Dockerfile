FROM ubuntu:18.04

RUN apt-get update && \
    apt-get install -y python3 && \
    apt-get install -y python3-pip && \
    pip3 install flask flask_sqlalchemy Flask_SQLAlchemy_session requests jsonify Response


WORKDIR /api

COPY . /api

EXPOSE 8080

CMD python3 createCustomdb.py ; python3 user.py

