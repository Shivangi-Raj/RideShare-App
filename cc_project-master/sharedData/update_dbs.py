import pika
import json 
from datetime import datetime
import time
import re
import requests
import enum
import csv
from flask import Flask,jsonify,Response,request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']='HELLOWORLD'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///persistent.db'
db = SQLAlchemy(app)
time.sleep(10)

class User(db.Model):
    username = db.Column(db.String(),primary_key=True,unique=True)
    password = db.Column(db.String(40))

class RideShare(db.Model):
    rideId = db.Column(db.Integer(),primary_key=True,unique=True,autoincrement=True)
    username = db.Column(db.String())
    timestamp = db.Column(db.String())
    # users = db.Column(db.String(),default="[]")
    source = db.Column(db.Integer())
    destination = db.Column(db.Integer())
class RideShare_User(db.Model):
    Id = db.Column(db.Integer(),primary_key=True,unique=True,autoincrement=True)
    rideId = db.Column(db.Integer())
    users = db.Column(db.String(),default="")



try:
    credentials=pika.PlainCredentials('guest','guest')
    parameters=pika.ConnectionParameters('rabbitmq','5672','/',credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='syncQ')
except:
    time.sleep(50)
finally:
    credentials=pika.PlainCredentials('guest','guest')
    parameters=pika.ConnectionParameters('rabbitmq','5672','/',credentials)
    connection = pika.BlockingConnection(parameters)
    # connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='syncQ')


def callback(ch, method, properties, body):
    count=0
    body=json.loads(body)
    print(body)
    tableName=body["tableName"]
    X=eval(tableName)
    func_Name=body["func_Name"]

    if func_Name=="create_user":
        new_user=X(username=body["username"],password=body["password"])
        print("in slaves  create_user")
        db.session.add(new_user)
        db.session.commit()
    
    if func_Name=="delete_user":
        username=body["username"]
        delete_user=User.query.filter_by(username=username).first()
        print("in delete user")
        db.session.delete(delete_user)
        db.session.commit()

    if func_Name=="create_ride":
        new_ride=X(username=body['username'],timestamp=body['timestamp'],source=body['source'],destination=body['destination'])
        db.session.add(new_ride)
        db.session.commit()

    if func_Name=="join_ride":
        new_ride=RideShare_User(rideId=body['rideId'],users=body['username'])
        db.session.add(new_ride)
        db.session.commit()

    if func_Name=="delete_ride":
        rideId=body["rideId"]
        ride = RideShare.query.filter_by(rideId=rideId).first()
        db.session.delete(ride)
        db.session.commit()

channel.basic_consume(
    queue='syncQ', on_message_callback=callback, auto_ack=True)

print(' [*] (UPDATEDB)  Waiting for messages. To exit press CTRL+C')
channel.start_consuming()


