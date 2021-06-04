#DATABSE USED ===== sqlite3  
import pika
import json 
from datetime import datetime
import time
import re
import requests
import enum
import csv
import sys
from flask import Flask,jsonify,Response,request
from flask_sqlalchemy import SQLAlchemy 

#--------------------------------------CREATING A DATABASE(master.db)-------------------------------------------------------------------------#
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']='HELLOWORLD'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///master.db'
db = SQLAlchemy(app)
time.sleep(10)
#-----------------------------------------------------------------------------------------------------------------------------------------------#
#-----------------------------------------DATA MODELS(TABLES DEFINED)----------------------------------------------------------------------------------------#
class User(db.Model):
    username = db.Column(db.String(),primary_key=True,unique=True)
    password = db.Column(db.String(40))

class RideShare(db.Model):
    rideId = db.Column(db.Integer(),primary_key=True,unique=True,autoincrement=True)
    username = db.Column(db.String())
    timestamp = db.Column(db.String())
    source = db.Column(db.Integer())
    destination = db.Column(db.Integer())
class RideShare_User(db.Model):
    Id = db.Column(db.Integer(),primary_key=True,unique=True,autoincrement=True)
    rideId = db.Column(db.Integer())
    users = db.Column(db.String(),default="")
#--------------------------------------------------------------------------------------------------------------------------------------------------------#

#-----------------------------------------------PIKA CONNECTION --------------------------------------------------------------------------------------#
try:
    credentials=pika.PlainCredentials('guest','guest')
    parameters=pika.ConnectionParameters('rabbitmq','5672','/',credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='writeQ')
    channel.queue_declare(queue='syncQ')
except:
    time.sleep(50)
finally:
    credentials=pika.PlainCredentials('guest','guest')
    parameters=pika.ConnectionParameters('rabbitmq','5672','/',credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='writeQ')#write request from the orchestrator
    channel.queue_declare(queue='syncQ')#for updating the slave db
#------------------------------------------------------------------------------------------------------------------------------------------------------------------#

#----------------------------------------------RESPONSE QUEUE FUNCTION---------------------------------------------------------------------------------------#
# in the function, the response stored in bodyA are returned to orchestrator
def responseQueue(body,ch,properties):
    response_body=json.dumps(body)
    ch.basic_publish(exchange="",routing_key='responseQ',properties=pika.BasicProperties(correlation_id=properties.correlation_id),body=response_body)

#-----------------------------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------CALLBACK FUNCTION----------------------------------------------------------------------------------------#
# In the function, the requested body is extracted and perticular operation is performed
def callback(ch, method, properties, body):
    body=json.loads(body)
    print(body)
    tableName=body["tableName"]
    func_Name=body["func_Name"]
    print(tableName)
    
    if func_Name=="create_user":
        X=eval(tableName)
        username=body["username"]
        user=User.query.filter_by(username=username).first()
        if user:
            print("if part")
            print(user)
            bodyA={"code":400,"response":"user already exist"}
            responseQueue(bodyA,ch,properties)

        else:
            print("else part")
            print(user)
            new_user=X(username=body["username"],password=body["password"])
            print("in  master create_user")
            db.session.add(new_user)
            db.session.commit()
            channel.basic_publish(exchange='', routing_key='syncQ', body=json.dumps(body))
            print(" master send msg to slave")
            bodyA={"code":201,"response":"user added to database"}
            responseQueue(bodyA,ch,properties)

    if func_Name=="delete_user":
        X=eval(tableName)
        username=body["username"]
        print(username)
        delete_user=User.query.filter_by(username=username).first()
        if not delete_user:
            bodyA={"code":400,"response":"delete userdoes not exist"}
            responseQueue(bodyA,ch,properties)
        else:
            print("in delete user")
            db.session.delete(delete_user)
            db.session.commit()
            channel.basic_publish(exchange='', routing_key='syncQ', body=json.dumps(body))
            print(" master send msg to slave")
            bodyA={"code":200,"response":"deleted from database"}
            responseQueue(bodyA,ch,properties)

    if func_Name=="create_ride":
        print("in create ride")
        X=eval(tableName)
        username=body["username"]
        user=User.query.filter_by(username=username).first()
        if not user:
            bodyA={"code":400,"response":" userdoes not exist"}
            responseQueue(bodyA,ch,properties)
        else:
            new_ride=X(username=body['username'],timestamp=body['timestamp'],source=body['source'],destination=body['destination'])
            db.session.add(new_ride)
            db.session.commit()
            channel.basic_publish(exchange='', routing_key='syncQ', body=json.dumps(body))
            print(" master send msg to slave")
            bodyA={"code":201,"response":"ride created"}
            responseQueue(bodyA,ch,properties)

    if func_Name=="join_ride":
        print("in join ride API")
        rideId=body['rideId']
        append_username=body['username']
        a=RideShare.query.filter_by(rideId=rideId).first()
        if not a:
            bodyA={"code":400,"response":" ride does not exist"}
            responseQueue(bodyA,ch,properties)
        else:
            user=User.query.filter_by(username=append_username).first()
            if not user:
                bodyA={"code":400,"response":" user does not exist"}
                responseQueue(bodyA,ch,properties)
            else:
                new_ride=RideShare_User(rideId=body['rideId'],users=body['username'])
                db.session.add(new_ride)
                db.session.commit()
                channel.basic_publish(exchange='', routing_key='syncQ', body=json.dumps(body))
                print(" master send msg to slave")
                bodyA={"code":200,"response":" user added"}
                responseQueue(bodyA,ch,properties)

    if func_Name=="delete_ride":
        print("in delete_ride API")
        rideId=body["rideId"]
        ride = RideShare.query.filter_by(rideId=rideId).first()
        if not ride:
            bodyA={"code":400,"response":" rideId does not exist"}
            responseQueue(bodyA,ch,properties)
        else:    
            db.session.delete(ride)
            db.session.commit()
            channel.basic_publish(exchange='', routing_key='syncQ', body=json.dumps(body))
            print(" master send msg to slave")
            bodyA={"code":200,"response":" user does not exist"}
            responseQueue(bodyA,ch,properties)
#----------------------------------------------------------------------------------------------------------------------------------------------------------#

#--------------------------------------------------------------------------------------------------------------------------------------------------------------#
#consuming the request of WRITEQ
channel.basic_consume(
    queue='writeQ', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
