import socket
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
import shutil
import socket
import docker
from kazoo.client import KazooClient,KazooState
import logging

#--------------------------------------------------------------------------------------#
# COPY DATA FROM ANOTHER FOLDER TO SLAVE DB 
path='/api/sd'
source ="/api/sd/persistent.db"
destination = "/api/slave.db"
dest = shutil.copyfile(source, destination) 
print('destination path:', dest)
#-----------------------------------------------------------------------------------------#

time.sleep(10)
client=docker.from_env()
client = docker.DockerClient(base_url='unix://var/run/docker.sock')
x_client = docker.APIClient(base_url='unix://var/run/docker.sock')
# -------------- ZOOKEEPER -----------------------------#
zk = KazooClient(hosts='zoo1:2181')

def my_listener(state):
    if state == KazooState.LOST:
        logging.warning("ZooKeeper connection Lost")
    elif state == KazooState.SUSPENDED:
        #Handle being disconnected from Zookeeper
        logging.warning("ZooKeeper connection Suspended")
    else:
        #Handle being connected/reconnected to Zookeeper
        logging.info("ZooKeeper Connected")

zk.add_listener(my_listener)
try:
    zk.start()
except:
    time.sleep(10)
finally:
    zk.start()
zk.ensure_path("/Workers/")
container=socket.gethostname()
container_current_obj= client.containers.get(container)
container_name_current=container_current_obj.name
container_pid_cur=x_client.inspect_container(container_name_current)['State']['Pid']

name="worker-" + str(container_pid_cur)
zk.create("/Workers/"+name,name.encode('utf-8')) 

#---------------------------------------------------------------------------#

#------------------------------CONNECTING FLASK AND CREATING A DB----------------------------------------------------------------------------------#
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']='HELLOWORLD'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///sd/persistent.db'

db = SQLAlchemy(app)
#----------------------------------------------------------------------------------------------------------------------------------------#
# ---------------------------------------------DATA MODELS-------------------------------------------------------------------------------#
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

#------------------------------------------------------------------------------------------#
#-----------------------------------------------------PIKA CONNECTION--------------------------------------------------------------------------#
try:
    credentials=pika.PlainCredentials('guest','guest')
    parameters=pika.ConnectionParameters('rabbitmq','5672','/',credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='readQ')
except:
    time.sleep(50)
finally:
    credentials=pika.PlainCredentials('guest','guest')
    parameters=pika.ConnectionParameters('rabbitmq','5672','/',credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='readQ')
#---------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------RESPONSE FUNCTION-----------------------------------------------------------------------------------------#
#FUNCTION in which the response is send back to orchestrator
def responseQueue(body,ch,properties):
    response_body=json.dumps(body)
    ch.basic_publish(exchange="",routing_key='responseQ',properties=pika.BasicProperties(correlation_id=properties.correlation_id),body=response_body)
#-----------------------------------------------------------------------------------------------------------------------------------------#
#check valid date
def valid_date(timedate):
    dt=datetime.now()
    current=dt.strftime("%d-%m-%Y:%S-%M-%H")
    pattern = '%d-%m-%Y:%S-%M-%H'
    epoch1 = int(time.mktime(time.strptime(current, pattern)))
    epoch2 = int(time.mktime(time.strptime(timedate, pattern)))
    if epoch1<epoch2:
        return 1
    else:
        return 0

#------------------------------------------------------------------------------------------------------------------------------------------------#
#callback function which extracts body from orchestrator and perticular operations are performed here
def callback(ch,method,properties,body):
    count=0

    print(body)
    body=json.loads(body)
    print("okayyyyyyyyyy")
    print(body)

    tableName=body["tableName"]
    X=eval(tableName)
    func_Name=body["func_Name"]
    print(tableName)
    if func_Name=='count_http_request_user':
        print("http_count_service")

    if func_Name=='get_all_users':
        print("get all users")
        X=eval(tableName)
        users = X.query.all()
        user_data= []
        for user in users:
            user_data.append(user.username)
        bodyA={"code":200,"response":user_data}
        responseQueue(bodyA,ch,properties)

    if func_Name=="count_ride":
        print("in the count ride")
        bodyA={"code":200,"response":"counting ride"}
        responseQueue(bodyA,ch,properties)
    
    if func_Name=='get_all_rides':
        print("in get all the rides")
        X=eval(tableName)
        rides = X.query.all()
        output = []
        for ride in rides:
            ride_data={}
            ride_data["rideId"] = ride.rideId
            ride_data["username"] = ride.username
            ride_data["timestamp"]=ride.timestamp
            ride_data["source"] = ride.source
            ride_data["destination"] = ride.destination
            output.append(ride_data)
        print(output)
        bodyA={"code":200,"response":output}
        responseQueue(bodyA,ch,properties)


    if func_Name=='get_specific_ride':
        print("in get specigic ride by source and destination")
        X=eval(tableName)
        source=body['source']
        destination=body['destination']
        if int(source)>198 or int(source)<1:
            bodyA={"code":400,"response":"{}"}
            responseQueue(bodyA,ch,properties)
            print("source does not exist")
        elif int(destination)>198 or int(destination)<1:
            print("destination does not exist")
            bodyA={"code":400,"response":"{}"}
            responseQueue(bodyA,ch,properties)
        else:
            rides = X.query.filter_by(source=source,destination=destination).all()
            output=[]
            for ride in rides:
                timedate=ride.timestamp
                vd=valid_date(timedate)
                
                if vd==1:

                    ride_data={}
                    ride_data['rideId']=ride.rideId
                    ride_data['username']=ride.username
                    ride_data['timestamp']=ride.timestamp

                    output.append(ride_data)
            print(output)
            if(len(output)==0):
                bodyA={"code":204,"response":output}

            else:
                bodyA={"code":200,"response":output}
            responseQueue(bodyA,ch,properties)
    
    if func_Name=="ride_details":
        print("in ride details given a ride")
        X=eval(tableName)
        rideId=body['rideId']
        rides = X.query.filter_by(rideId=rideId).all()
        rideShares=RideShare_User.query.filter_by(rideId=rideId)
        users=[i.users for i in rideShares]
        print(users)
        output=[]
        if not rides:
            print("ride does not exist")
            bodyA={"code":400,"response":"{}"}
            responseQueue(bodyA,ch,properties)    
        else:        
            for ride in rides:
                ride_data={}
                ride_data['rideId']=ride.rideId
                ride_data['created_by']=ride.username
                ride_data['users']=users
                ride_data['timestamp']=ride.timestamp
                ride_data['source']=ride.source
                ride_data['destination']=ride.destination
                output.append(ride_data)
        print(output)
        bodyA={"code":200,"response":output}
        responseQueue(bodyA,ch,properties)
    
    if func_Name=='count_http_request_ride':
        print("in count http request ride")
#--------------------------------------------------------------------------------------------------------------------------------------#

channel.basic_consume(queue='readQ', on_message_callback=callback, auto_ack=True)

print(' [*] (SLAVE)Waiting for messages. To exit press CTRL+C')
channel.start_consuming()


