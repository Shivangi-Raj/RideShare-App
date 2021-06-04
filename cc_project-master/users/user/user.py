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

db = SQLAlchemy(app)
count=0

# Joining new user in the existing list
def users_list(users,new_user):
    user = ""
    u=[]
    for i in range(len(users)):
        if users[i] in ('[',']','\'',' '):
            continue
        else:
            user = user+users[i]
    if user=="":
        u.append(new_user)
    else:
        u= user.split(',')
        u.append(new_user)
    return str(u)

# REST API'S
#get all the users and there password present
get_user=[]
@app.route("/",methods={"GET"})
def example():
    return "hello world"

@app.route('/api/v1/users', methods={'GET'})
def get_all_users():
    global count
    count=count+1
    tableName='User'
    func_Name="get_all_users"
    print(func_Name)
    user={"tableName":tableName,"func_Name":func_Name}
    get_user=requests.post("http://34.194.180.47:80/api/v1/db/read",json=user)
    return Response(get_user)
    r='{}'
    return Response(get_user,status=get_user.status_code,mimetype="application/json")

#----------TASK 1:-------
#create an user and add in db
@app.route('/api/v1/users', methods={'PUT'})
def create_user():
    global count
    count=count+1
    data = request.get_json()
    l=[]
    for i in data.keys():
        l.append(i)
    if l!=['username','password']:
            return {},400
    username=data['username']
    password=data['password']
    tableName='User'
    func_Name='create_user'
    new_user={"tableName":tableName,"func_Name":func_Name,"username":username,"password":password}
    x=re.search("^[0-9a-fA-F]{40}$",password)
    if not(x):
        return {},400

    s=requests.post("http://34.194.180.47:80/api/v1/db/write",json=new_user)
    print(s)
    r='{}'
    return Response(r,status=s.status_code,mimetype="application/json")


#----------TASK 2:-------
#Remove the existing user
@app.route('/api/v1/users/<username>', methods={'DELETE'})
def delete_user(username):
    global count
    count=count+1
    print(username)
    tableName='User'
    func_Name='delete_user'
    new_user={"tableName":tableName,"func_Name":func_Name,"username":username}
    s=requests.post("http://34.194.180.47:80/api/v1/db/write",json=new_user)
    r='{}'
    return Response(r,status=s.status_code,mimetype="application/json")


# CLEAR DB
@app.route('/api/v1/db/clear', methods={'POST'})
def clear_db_user():
    global count
    count=count+1
    tableName='User'
    func_Name='clear_db_user'

    new_user={"tableName":tableName,"func_Name":func_Name}
    s=requests.post("http://34.194.180.47:80/api/v1/db/write",json=new_user)
    r='{}'
    return Response(r,status=s.status_code,mimetype="application/json")

#4 COUNT HTTP REQUESTS TO MICROSERVICES
@app.route('/api/v1/_count', methods={'GET'})
def count_http_request_user():
    return "["+str(count)+"]"


#5 RESET COUNT TO 0
@app.route('/api/v1/_count', methods={'DELETE'})
def count_reset_user():
    global count
    count=0
    return {},200

if __name__=='__main__':
     app.run(host="0.0.0.0",port=8080,debug=True)
