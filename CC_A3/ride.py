import json
from datetime import datetime
import time
import re
import enum
import csv
from flask import Flask,request,jsonify,Response
from flask_sqlalchemy import SQLAlchemy
import sys
# from user import get_all_users

# print(get_all_users.user_data)
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']='HELLOWORLD'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///ride.db'
debug=False
ALLOWED_HOST = ["*"]

count=0
count_rides=0
db = SQLAlchemy(app)
res = app.test_client()

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
    new_ride = RideShare(username=data['created_by'],timestamp=data['timestamp'],source=data['source'],destination=data['destination'])
    timedate=new_ride.timestamp

    y=re.search("[0-3]\d-[0-1]\d-\d\d\d\d:[0-6]\d-[0-6]\d-([0-1][0-9]|2[0-4])",timedate)

    if not(y):
        return {},400

    vd=valid_date(timedate)

    if vd==0:
        return {},400

    users=new_ride.username
    # user = User.query.filter_by(username=users).first()
    r = res.get("http://user:80/api/v1/users")
    print(r)



    if not r:
        return {},400

    new_ride_json={"tableName":tableName,"func_Name":func_Name,"username":new_ride.username,"timestamp":new_ride.timestamp,"source":new_ride.source,"destination":new_ride.destination}

    s=res.post("http://localhost:80/api/v1/db/write",json=new_ride_json)
    return { },201

# EXAMPLE::
# Get all the rides of the db
@app.route('/ride', methods=['GET'])
def get_all_rides():
    tableName='RideShare'
    func_Name='get_all_rides'
    get_ride={"tableName":tableName,"func_Name":func_Name}
    rides=res.post("http://localhost:80/api/v1/db/read",json=get_ride)
    return rides

#----------TASK 4:-------
# List all upcoming rides for a given source and destination
@app.route('/api/v1/rides', methods=['GET'])
def get_specific_ride():
    global count
    count=count+1
    source=request.args.get("source")
    destination=request.args.get("destination")
    tableName='RideShare'
    func_Name='get_specific_ride'

    get_ride={"tableName":tableName,"func_Name":func_Name,"source":source,"destination":destination}
    rides=res.post("http://localhost:80/api/v1/db/read",json=get_ride)
    return rides


#----------TASK 5:-------
# List all the details of a given ride
@app.route('/api/v1/rides/<rideId>', methods=['GET'])
def ride_details(rideId):
    global count
    count=count+1
    # rideId=request.args.get("rideId")
    tableName='RideShare'
    func_Name='ride_details'
    get_ride={"tableName":tableName,"func_Name":func_Name,"rideId":rideId}

    rides=res.post("http://localhost:80/api/v1/db/read",json=get_ride)
    # print(rides)
    return rides

#----------TASK 6:-------
# Joining the existing ride
@app.route('/api/v1/rides/<rideId>', methods=['POST'])
def join_ride(rideId):
    global count
    count=count+1
    # return jsonify({"s2":rideId})
    tableName='RideShare_User'
    func_Name='join_ride'
    data = request.get_json()
    append_user={"tableName":tableName,"func_Name":func_Name,"rideId":rideId,"username":data['username']}

    rides=res.post("http://localhost:80/api/v1/db/write",json=append_user)
    return {},200


#----------TASK 7:-------
# Delete the ride
@app.route('/api/v1/rides/<rideId>', methods=['DELETE'])
def delete_ride(rideId):
    global count_rides
    global count
    count=count+1
    count_rides=count_rides-1
    tableName='RideShare'
    # method='DELETE'
    delete_ride={"tableName":tableName,"func_Name":"delete_ride","rideId":rideId}
    s=res.post("http://localhost:80/api/v1/db/write",json=delete_ride)
    return {},200


# CLEAR DB
@app.route('/api/v1/db/clear', methods=['POST'])
def clear_db():
    global count
    count=count+1
    tableName='User'
    func_Name='clear_db'

    new_user={"tableName":tableName,"func_Name":func_Name}
    s=res.post("http://localhost:80/api/v1/db/write",json=new_user)
    return s

#8 COUNT HTTP REQUESTS TO MICROSERVICES
@app.route('/api/v1/_count', methods=['GET'])
def count_http_request():
    func_Name="count_http_request"
    # return "hello"
    tableName='User'
    new_user={"tableName":tableName,"func_Name":func_Name}
    # return "hell"
    s=res.post("http://localhost:80/api/v1/db/read",json=new_user)
    # l=[]
    # l.append(s["count"])    
    return s
#9 RESET COUNT TO 0
@app.route('/api/v1/_count', methods=['DELETE'])
def count_reset():
    func_Name='count_reset'
    tableName='User'
    new_user={"tableName":tableName,"func_Name":func_Name}
    s=res.post("http://localhost:80/api/v1/db/write",json=new_user)
    return s


#10 COUNT NUMBER OF RIDES
@app.route('/api/v1/rides/count', methods=['GET'])
def count_ride():
    func_Name='count_ride'
    tableName='User'  
    new_user={"tableName":tableName,"func_Name":func_Name}
    s=res.post("http://localhost:80/api/v1/db/read",json=new_user)
    return s

#----------TASK 8:-------
#Write to db
@app.route('/api/v1/db/write', methods=['POST'])
def write_to_db():
    data=request.get_json()
    tableName=data["tableName"]
    X=eval(tableName)
    func_Name=data['func_Name']

    #3. Create a new ride
    if tableName=='RideShare' and func_Name=='create_ride':
        X=eval(tableName)
        new_ride=X(username=data['username'],timestamp=data['timestamp'],source=data['source'],destination=data['destination'])
        
        db.session.add(new_ride)
        db.session.commit()
        return ""


    #6. Join an existing ride
    if tableName=='RideShare_User' and func_Name=='join_ride':
        # print("entered",file=sys.stdout)
        rideId=data['rideId']
        append_username=data['username']
        # a=db.session.query(RideShare).filter_by(rideId=rideId).first
        ride = RideShare.query.filter_by(rideId=rideId).first()
        # print(ride,RideShare,file=sys.stdout)
        # print(ride.rideId)
        if(db.session.query(RideShare).filter_by(rideId=rideId).count()):
            r = res.get("http://user:80/api/v1/users")
            # print(r)
            if not r:
                return {},400
            else:
                new_ride=RideShare_User(rideId=data['rideId'],users=data['username'])
                db.session.add(new_ride)
                db.session.commit()
                return {},200
        else:
                
                return {},400



    #7. Delete a ride
    if tableName=='RideShare' and func_Name=='delete_ride':
        X=eval(tableName)
        rideId=data['rideId']
        ride = RideShare.query.filter_by(rideId=rideId).first()
        if not ride:
            return {},400
        db.session.delete(ride)
        db.session.commit()
        return ""

    #8.clear the db
    if tableName=='User' and func_Name=='clear_db':
        db.session.query(User).delete()
        db.session.commit()
        return {},200
    #9.reset count
    if tableName=='User' and func_Name=='count_reset':
        global count
        count=0
        return {},200


#----------TASK 9:-------
#Read from db
@app.route('/api/v1/db/read', methods=['POST'])
def read_to_db():
    data=request.get_json()
    tableName=data['tableName']
    func_Name=data['func_Name']
    X=eval(tableName)

        # example to get all rides
    if tableName=='RideShare' and func_Name=='get_all_rides':
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
        return jsonify(output)

    #4. List all upcoming rides for a given source and destination
    if tableName=='RideShare' and func_Name=='get_specific_ride':
        source=data['source']
        destination=data['destination']
        # print(type(int(source)))
        if int(source)>198 or int(source)<1:
            return {},400
        if int(destination)>198 or int(destination)<1:
            return {},400
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

        return jsonify(output) ,200

    # 5. List all the details of a given ride
    if tableName=='RideShare' and func_Name=='ride_details':
        # rideId=request.args.get("rideId")
        rideId=data["rideId"]
        rides = X.query.filter_by(rideId=rideId).all()
        rideShares=RideShare_User.query.filter_by(rideId=rideId)
        users=[i.users for i in rideShares]
        output=[]
        if not rides:
            return {},400
        for ride in rides:
            users.append(ride.username)
            ride_data={}
            ride_data['rideId']=ride.rideId
            ride_data['created_by']=ride.username
            ride_data['users']=users
            ride_data['timestamp']=ride.timestamp
            ride_data['source']=ride.source
            ride_data['destination']=ride.destination
            output.append(ride_data)
        # print(output)
        return jsonify(output)

    #4 count http request
    if tableName=='User' and func_Name=='count_http_request':
        return "["+str(count)+"]"
    #10 count no of rides
    if tableName=='User' and func_Name=='count_ride':
        c={}
        c['count_rides']=count_rides
        return c
    
    


if __name__=='__main__':
    app.run('0.0.0.0',port=80,debug=True)
