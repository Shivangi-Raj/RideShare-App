#DATABASE=========sqlite3
import json
from datetime import datetime
import requests
import time
import re
import enum
import csv
from flask import Flask,request,jsonify,Response
from flask_sqlalchemy import SQLAlchemy
import sys
app = Flask(__name__)

count=0#count no of http request
count_rides=0 # count total no. of rides
db = SQLAlchemy(app)

# Validation of date :::
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



#----------TASK 3:-------
# Create a new ride::
@app.route('/api/v1/rides', methods=['POST'])
def create_ride():
    global count
    global count_rides
    count=count+1
    count_rides=count_rides+1
    data = request.get_json()
    l=[]
    for i in data.keys():
        l.append(i)
    if l!=['created_by','timestamp','source','destination']:
            return {},400
    tableName='RideShare'
    func_Name='create_ride'
    timedate=data["timestamp"]
    y=re.search("[0-3]\d-[0-1]\d-\d\d\d\d:[0-6]\d-[0-6]\d-([0-1][0-9]|2[0-4])",timedate)

    if not(y):
        return {},400

    vd=valid_date(timedate)

    if vd==0:
        return {},400

    new_ride_json={"tableName":tableName,"func_Name":func_Name,"username":data['created_by'],"timestamp":data['timestamp'],"source":data['source'],"destination":data['destination']}
    s=requests.post("http://34.194.180.47:80/api/v1/db/write",json=new_ride_json)
    r='{}'
    return Response(r,status=s.status_code,mimetype="application/json")



# # EXAMPLE::
# # Get all the rides of the db
@app.route('/rides', methods={'GET'})
def get_all_rides():
    tableName='RideShare'
    func_Name='get_all_rides'
    get_ride={"tableName":tableName,"func_Name":func_Name}
    rides=requests.post("http://34.194.180.47:80/api/v1/db/read",json=get_ride)
    r='{}'
    return Response(rides,status=rides.status_code,mimetype="application/json")

# #----------TASK 4:-------
# # List all upcoming rides for a given source and destination
@app.route('/api/v1/rides', methods=['GET'])
def get_specific_ride():
    global count
    count=count+1
    source=request.args.get("source")
    destination=request.args.get("destination")
    print(source)
    print(destination)
    tableName='RideShare'
    func_Name='get_specific_ride'
    get_ride={"tableName":tableName,"func_Name":func_Name,"source":source,"destination":destination}
    rides=requests.post("http://34.194.180.47:80/api/v1/db/read",json=get_ride)
    print(rides)
    return Response(rides,status=rides.status_code)


# #----------TASK 5:-------
# # List all the details of a given ride
@app.route('/api/v1/rides/<rideId>', methods=['GET'])
def ride_details(rideId):
    global count
    count=count+1
    print(rideId)
    tableName='RideShare'
    func_Name='ride_details'
    get_ride={"tableName":tableName,"func_Name":func_Name,"rideId":rideId}
    rides=requests.post("http://34.194.180.47:80/api/v1/db/read",json=get_ride)
    print(rides)
    l= json.loads(rides.text)
    s= Response(rides.text,status=rides.status_code,mimetype="application/text")
    return s    

# #----------TASK 6:-------
# # Joining the existing ride
@app.route('/api/v1/rides/<rideId>', methods=['POST'])
def join_ride(rideId):
    global count
    count=count+1
    tableName='RideShare_User'
    func_Name='join_ride'
    print(rideId)
    data = request.get_json()
    print(data)
    append_user={"tableName":tableName,"func_Name":func_Name,"rideId":rideId,"username":data['username']}
    rides=requests.post("http://34.194.180.47:80/api/v1/db/write",json=append_user)
    r='{}'
    return Response(r,status=rides.status_code,mimetype="application/json")


# #----------TASK 7:-------
# # Delete the ride
@app.route('/api/v1/rides/<rideId>', methods=['DELETE'])
def delete_ride(rideId):
    global count_rides
    global count
    count=count+1
    count_rides=count_rides-1
    tableName='RideShare'
    func_Name="delete_ride"
    delete_ride={"tableName":tableName,"func_Name":func_Name,"rideId":rideId}
    s=requests.post("http://34.194.180.47:80/api/v1/db/write",json=delete_ride)
    r='{}'
    return Response(r,status=s.status_code,mimetype="application/json")



# CLEAR DB
@app.route('/api/v1/db/clear', methods=['POST'])
def clear_db_ride():
    global count
    count=count+1
    tableName='RideShare'
    func_Name='clear_db_ride'

    new_user={"tableName":tableName,"func_Name":func_Name}
    s=requests.post("http://34.194.180.47:80/api/v1/db/write",json=new_user)
    r='{}'
    return Response(r,status=s.status_code,mimetype="application/json")

# #8 COUNT HTTP REQUESTS TO MICROSERVICES
@app.route('/api/v1/_count', methods=['GET'])
def count_http_request_ride():
    global count
    c=json.dumps(count)
    return '['+str(count)+']'

# #9 RESET COUNT TO 0
@app.route('/api/v1/_count', methods=['DELETE'])
def count_reset_ride():
    global count
    count=0
    return {},200


# #10 COUNT NUMBER OF RIDES
@app.route('/api/v1/rides/count', methods={'GET'})
def count_ride():
    global count_rides
    return '['+str(count_rides)+']'
if __name__=='__main__':
    app.run('0.0.0.0',port=8000,debug=False)
