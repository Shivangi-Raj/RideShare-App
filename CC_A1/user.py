import json
from datetime import datetime
import time
import re
import enum
import csv
from flask import Flask,request,jsonify,Response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']='HELLOWORLD'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///ride.db'
debug=False
ALLOWED_HOST = ["*"]

db = SQLAlchemy(app)
res = app.test_client()
# TABLES
class User(db.Model):
	username = db.Column(db.String(),primary_key=True,unique=True)
	password = db.Column(db.String(40))

#FUNCTIONS:::::


# Joining new user in the existing list
def users_list(users,new_user):
   #(eg: users=['c'] , new_user='b', u=['c','b'])
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
#
#get all the users and there password present
# get_user=[]
@app.route('/api/v1/users', methods=['GET'])
def get_all_users():
    tableName='User'
    func_Name='get_all_users'
    user={"tableName":tableName,"func_Name":func_Name}
    get_user=res.post('http://127.0.0.1:5000/api/v1/db/read',json=user)
    return get_user
#----------TASK 1:-------
#create an user and add in db
@app.route('/api/v1/users', methods=['PUT'])
def create_user():
    data = request.get_json()
    l=[]
    for i in data.keys():
        l.append(i)
    if l!=['username','password']:
            return {},400
    username=data['username']
    password=data['password']

    user = User.query.filter_by(username=username).first()
    print(user)
    if user:
        return {},400
    tableName='User'
    func_Name='create_user'
    new_user={"tableName":tableName,"func_Name":func_Name,"username":username,"password":password}
    password=password
    x=re.search("^[0-9a-fA-F]{40}$",password)
    if not(x):
        return {},400
    s=res.post("http://127.0.0.1:5000/api/v1/db/write",json=new_user)
    
    return {},201


#----------TASK 2:-------
#Remove the existing user
@app.route('/api/v1/users/<username>', methods=['DELETE'])
def delete_user(username):
    # username=request.args.get("username")
    tableName='User'
    func_Name='delete_user'
    delete_users=User.query.filter_by(username=username).first()
    if delete_users==None:
        return {},400
    new_user={"tableName":tableName,"func_Name":func_Name,"username":username}
    s=res.post("http://127.0.0.1:5000/api/v1/db/write",json=new_user)
    return s


# CLEAR DB
@app.route('/api/v1/db/clear', methods=['POST'])
def clear_db():

    tableName='User'
    func_Name='clear_db'

    new_user={"tableName":tableName,"func_Name":func_Name}
    s=res.post("http://127.0.0.1:5000/api/v1/db/write",json=new_user)
    return s


#----------TASK 8:-------
#Write to db
@app.route('/api/v1/db/write', methods=['POST'])
def write_to_db():
    data=request.get_json()
    tableName=data["tableName"]
    X=eval(tableName)
    func_Name=data['func_Name']
    #1. Add user
    if tableName=='User' and func_Name=='create_user':
        
        new_user=X(username=data['username'],password=data['password'])
        db.session.add(new_user)
        db.session.commit()
        return "done"
    #2. Remove user
    if tableName=='User' and func_Name=='delete_user':
        username=data['username']
        X=eval(tableName)
        delete_user=User.query.filter_by(username=username).first()
        db.session.delete(delete_user)
        db.session.commit()
        return {},200
    #3.clear the db
    if tableName=='User' and func_Name=='clear_db':
        db.session.query(User).delete()
        db.session.commit()
        return {},200
#----------TASK 9:-------
#Read from db
@app.route('/api/v1/db/read', methods=['POST'])
def read_to_db():
    data=request.get_json()
    tableName=data['tableName']
    func_Name=data['func_Name']
    X=eval(tableName)

    #Get all users
    if tableName=='User' and func_Name=='get_all_users':
        users = X.query.all()
        user_data= []
        for user in users:
            # user_data=[]
            user_data.append(user.username)
            # user_data["password"] = user.password
            # output.append(user_data)
        return jsonify(user_data)

if __name__=='__main__':
     app.run(debug=True)