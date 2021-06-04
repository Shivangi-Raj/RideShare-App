FROM ubuntu:18.04

RUN apt update && \
    apt install -y python3 && \
    apt-get install -y python3-pip && \
    pip3 install flask sqlalchemy Flask_SQLAlchemy_session requests


WORKDIR /app
# WORKDIR /ride
COPY . /app

EXPOSE 8000
# ADD . /user
# ADD . /ride

# RUN pip3 install -r requirements.txt
CMD ["python3", "ride.py"]
# CMD ["python3", "ride.py"]

# docker-compose up
# user:
# docker build