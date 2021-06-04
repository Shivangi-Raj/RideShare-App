#DATABASE USED ==== sqlite3
import docker
import json
from datetime import datetime
import time
import re
import enum
import uuid
import csv
from flask import Flask,request,jsonify,Response
import pika
import sys
import math
import threading
from kazoo.client import KazooClient,KazooState
import logging
logging.basicConfig()

#FLASK connection
app=Flask(__name__)

#Docker connection
client = docker.from_env()
count=0 # no of read requests
time_start0=False
time_started1=False
dict_index=0 # initial dictionary index of list_container
list_container={} # dictionary of all the containers present
pid_of_container=[] # pid of container
client = docker.DockerClient(base_url='unix://var/run/docker.sock')
x_client = docker.APIClient(base_url='unix://var/run/docker.sock')

time.sleep(30)


#---CREATING 1ST SLAVE CONTAINER--------------------------------------------------------------------------------------------------------# 

list_container[dict_index] = client.containers.run("slave:latest", command =["python3","slave.py","1"],detach=True,network = 'ccproject_default',volumes = {'/home/ubuntu/cc_project/sharedData/':{'bind': '/api/sd'}})
try:
    cont_name=list_container[dict_index].name
except:
    cont_name=list_container[dict_index].Name
pid= x_client.inspect_container(cont_name)['State']['Pid']
pid_of_container.append(pid)
dict_index=dict_index+1
#------------------------------------------------------------------------------------------------------------------------------------#

#-----------------------------------------------ZOOKEEPER---------------------------------------------------------------------------------#
zk=KazooClient(hosts="zoo1:2181")

def my_listener(state):
    if state == KazooState.LOST:
        # Register somewhere that the session was lost
        logging.warning("Registerd somewhere that the session was lost")
    elif state == KazooState.SUSPENDED:
        # Handle being disconnected from Zookeeper
        logging.warning("suspended")
    else:
        # Handle being connected/reconnected to Zookeeper
        logging.info("zookeeper is connected")

zk.add_listener(my_listener)
try:
    zk.start()
except:
    time.sleep(10)
finally:
    zk.start()

if(zk.exists("/Workers")):
    zk.delete("/Workers",recursive=True)

if(zk.exists("/Slave")):
    zk.delete("/Slave",recursive=True)

zk.ensure_path("/Slave/")

@zk.ChildrenWatch("/Workers/",send_event=True)
def watch(children,event):
    print("in zookeeper event")
    if event ==None:
        pass
    elif event.type is DELETED:
        print("slave deleted")
    elif event.type is CREATED:
        leader = None
        for i in children:
            pid=int(i.split("-")[1])
            if leader == None:
                leader=pid
            if pid<leader:
                leader=pid
        if(zk.exists("/Slave")):
            zk.delete("/Slave")
            zk.create("/Slave/"+"worker-"+str(leader),str(leader).encode(utf-8))# selects the leader os slaves


#------------------------------------------------------------------------------------------------------------------------------------#

def time_start():
    global time_start0
    global time_started1
    if(not(time_started1) and (time_start0)):
        time_started1=True
        timefunc()
#---------------------------------------------------SCALING & SPAWNING FUNCTION-----------------------------------------------------
def timefunc():
    print("in the timer function")
    global count
    global list_container
    global pid_of_container
    global dict_index
    global client
    global x_client

    total_slaves=0
    #NUMBER OF SLAVES
    total_slaves=int(math.ceil(count/2))
    if(total_slaves == 0):
        total_slaves = 1
    n=len(list_container)
    #------SWAPING MULTIPLE SLAVES--------------------------------------------------#
    if(n<=total_slaves):
        print("less slaves present")
        print("initial container",list_container)
        for i in range(n,total_slaves):
            print("range")
            list_container[dict_index] = client.containers.run("slave:latest", command =["python3","slave.py","1"],detach=True,network = 'ccproject_default',volumes = {'/home/ubuntu/cc_project/sharedData/':{'bind': '/api/sd'}})
            try:
                cont_name=list_container[dict_index].name
            except:
                cont_name=list_container[dict_index].Name
            pid= x_client.inspect_container(cont_name)['State']['Pid']
            pid_of_container.append(pid)
            dict_index=dict_index+1
        print("range11")
    elif(n>total_slaves):
        print("more slaves present")
        while(n>total_slaves):
            for i in range(1,len(list_container)):
                max_pid_pos=0
                curr_pid=x_client.inspect_container(list_container[i].name)['State']['Pid']
                max_pid=x_client.inspect_container(list_container[max_pid_pos].name)['State']['Pid']
                if(list_container[i] and curr_pid>max_pid):
                    max_pid_pos=i

            list_container[max_pid_pos].stop()
            list_container[max_pid_pos].remove()
            del list_container[max_pid_pos]
            pid_of_container.remove(max_pid)
            print(pid_of_container)
#TIMER FOR CALCULATING NO OF SLAVES IN EVERY 2 MINUTES -------------------------------------#
            count=0
            restart = threading.Timer(10,timefunc)
            restart.start()
#--------------------------------------------------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------RPCClient CLASS-----------------------------------------------------------------------------------------#
#CLASS through which message is passed to the respective master and slaves
class RPCClient(object):
    rpcServer="readQ"
    body_send=json.dumps({})
    corr_id=None
    def __init__(self,body,rpcServer):
        self.rpcServer=rpcServer
        self.body_send=body
#---------------------------------PIKA CONNECTION-----------------------------------------------------------------------------------#
        self.credentials=pika.PlainCredentials('guest','guest')
        self.parameters=pika.ConnectionParameters('rabbitmq','5672','/',self.credentials)
        self.connection = pika.BlockingConnection(self.parameters)
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(queue='responseQ')
        self.channel.basic_qos(prefetch_count=0)
        self.channel.basic_consume(on_message_callback=self.callbackResponse, queue='responseQ')
        self.channel.queue_declare(queue='readQ')
        self.channel.queue_declare(queue='writeQ')
  #-----------------------------------------------------------------------------------------------------------------------------------#  
    def callbackResponse(self,ch,methods,props,body):
        if self.corr_id == props.correlation_id:
            body=json.loads(body)
            self.response=body
            print(self.response)
    
    def call(self):
        self.response=None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange="", routing_key=self.rpcServer, properties = pika.BasicProperties(reply_to = 'responseQ',correlation_id = self.corr_id),body = self.body_send)

        while self.response is None:
            self.connection.process_data_events()
        
        self.connection.close()
        return self.response

#----------TASKS :-------
# CLEAR DB
@app.route('/api/v1/db/clear', methods=['POST'])
def clear_db_ride():
    data={"func_Name":"clear_db_ride","tableName":"User"}
    data["message"]="read_ride"
    newClient = RPCClient(json.dumps(data),'writeQ')
    res = newClient.call()
    print(res["code"])
    print(res["response"])
    return {},200

#Write to db
@app.route('/api/v1/db/write', methods=['POST'])
def write_to_db():
    data=request.get_json()
    print(data)
    tableName=data["tableName"]
    func_Name=data['func_Name']
    # #1. Add user
    if func_Name=='create_user':
        data["message"]="write_user"
        newClient = RPCClient(json.dumps(data),'writeQ')
        res = newClient.call()
        print(res["code"])
        print(res["response"])
        return Response(res,status=res["code"],mimetype="application/json")
    # #2. Remove user
    if func_Name=='delete_user':
        data["message"]="write_user"
        newClient = RPCClient(json.dumps(data),'writeQ')
        res = newClient.call()
        print(res["code"])
        print(res["response"])
        return Response(res,status=res["code"],mimetype="application/json")
    # #3.clear the db
    if func_Name=='clear_db_user':
        data["message"]="write_user"
        newClient = RPCClient(json.dumps(data),'writeQ')
        res = newClient.call()
        print(res["code"])
        print(res["response"])
        return Response(res,status=res["code"],mimetype="application/json")
    #3. Create a new ride
    if func_Name=='create_ride':
        data["message"]="write_ride"
        newClient = RPCClient(json.dumps(data),'writeQ')
        res = newClient.call()
        print(res["code"])
        print(res["response"])
        return Response(res,status=res["code"],mimetype="application/json")
    #6. Join an existing ride
    if func_Name=='join_ride':
        print("entered")
        rideId=data['rideId']
        data["message"]="write_ride"
        newClient = RPCClient(json.dumps(data),'writeQ')
        res = newClient.call()
        print(res["code"])
        print(res["response"])
        return Response(res,status=res["code"],mimetype="application/json")
    #7. Delete a ride
    if func_Name=='delete_ride':
        data["message"]="write_ride"
        newClient = RPCClient(json.dumps(data),'writeQ')
        res = newClient.call()
        print(res["code"])
        print(res["response"])
        return Response(res,status=res["code"],mimetype="application/json")
        

#Read from db
@app.route('/api/v1/db/read', methods={'POST'})
def read_to_db():
    print("inside read")
    data=request.get_json()
    tableName=data['tableName']
    func_Name=data['func_Name']
    global time_start0
    global count
    time_start0=True
    count=count+1
    time_start() # START OF THE TIMER FUNCTION

    # Get all users
    if func_Name=='get_all_users':
        data["message"]="read_user"
        newClient = RPCClient(json.dumps(data),'readQ')
        res = newClient.call()
        print(res["code"])
        print(res["response"])
        return Response(res["response"],status=res["code"],mimetype="application/json")   
    # example to get all rides
    if func_Name=='get_all_rides':
        data["message"]="read_ride"
        newClient = RPCClient(json.dumps(data),'readQ')
        res = newClient.call()
        print(res["code"])
        print(res["response"])
        r=json.dumps(res["response"],indent=4)
        print(r)
        return Response(r,status=res["code"],mimetype="application/json")
    #4. List all upcoming rides for a given source and destination
    if func_Name=='get_specific_ride':
        data["message"]="read_ride"
        newClient = RPCClient(json.dumps(data),'readQ')
        res = newClient.call()
        print(res["code"])
        print(res["response"])
        r=json.dumps(res["response"],indent=4)
        print(r)
        if(res["response"]=="{}"):
            return Response(res["response"],status=res["code"],mimetype="application/json")
        else:
            return Response(r,status=res["code"],mimetype="application/json")
    # 5. List all the details of a given ride
    if func_Name=='ride_details':
        print("in ride details")
        data["message"]="read_ride"
        newClient = RPCClient(json.dumps(data),'readQ')
        res = newClient.call()
        print("doneee")
        print(res["code"])
        print(res["response"])
        r=json.dumps(res["response"],indent=4)
        print("********************************************************************")
        if(res["response"]=="{}"):
            return Response(res["response"],status=res["code"],mimetype="application/json")
        else:
            return Response(r,status=res["code"],mimetype="application/json")
    #10 count no of rides
    if func_Name=='count_ride':
        data["message"]="read_ride"
        newClient = RPCClient(json.dumps(data),'readQ')
        res = newClient.call()
        print("doneee")
        print(res["code"])
        print(res["response"])
        r=json.dumps(res["response"],indent=4)
        print(r)
        if(res["response"]=="{}"):
            return Response(res["response"],status=res["code"],mimetype="application/json")
        else:
            return Response(r,status=res["code"],mimetype="application/json")
#------------------------------------------------------------------EXAMPLE API---------------------------------------------------------------------------------------------------------------------------------------------------#
#just to check if our orchestrator is connected or not
@app.route("/", methods={"GET"})
def a():
    return "cool"
#-----------------------------------------------------------------------------------------------------------------------------------------------#

#-----------------------------------------------------------------CRASH SLAVE API------------------------------------------------------------------------------------------------------------------------------------------#
#deletes the slave container with max pid, and creates another slave container
@app.route('/api/v1/crash/slave', methods={'POST'})
def crash_slave():
    func_Name='crash_slave'
    global pid_of_container
    global list_container
    global dict_index
    print(pid_of_container)
    max_pid_pos=0
    for i in range(len(pid_of_container)):
        curr_pid=x_client.inspect_container(list_container[i].name)['State']['Pid']
        max_pid=x_client.inspect_container(list_container[max_pid_pos].name)['State']['Pid']
        if(list_container[i] and curr_pid>max_pid):
            max_pid_pos=i
    list_container[max_pid_pos].stop()
    list_container[max_pid_pos].remove()
    del list_container[max_pid_pos]
    max_pid=max(pid_of_container)
    pid_of_container.remove(max_pid)
    list_container[dict_index] = client.containers.run("slave:latest", command =["python3","slave.py","1"],detach=True,network = 'ccproject_default',volumes = {'/home/ubuntu/cc_project/sharedData/':{'bind': '/api/sd'}})
    try:
        cont_name=list_container[dict_index].name
    except:
        cont_name=list_container[dict_index].Name
    ppid= x_client.inspect_container(cont_name)['State']['Pid']
    pid_of_container.append(ppid)
    dict_index=dict_index+1
    m=[]
    m.append(max_pid)
    return Response(json.dumps(str(m)),status = 200,mimetype= "application/json")

#------------------------------------------------------------WORKER LIST API--------------------------------------------------------------------------------------------------------------------------------#
#lists the pid of all the slaves running
@app.route('/api/v1/worker/list', methods={'GET'})
def workers_list():
    func_Name="worker_list"
    global pid_of_container
    print(pid_of_container)
    pid_of_container.sort()
    return Response(json.dumps(str(pid_of_container)),status=200,mimetype="application/json")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------#

if __name__=='__main__':
     app.run(host="0.0.0.0",port=3002,debug=True)

