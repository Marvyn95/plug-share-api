from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from datetime import datetime
import json
import pymongo
from bson import ObjectId
from flask_bcrypt import Bcrypt

# app initialization
app = Flask(__name__)
api = Api(app)

# MongoDB setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["plugshare_db"]

# Bcrypt setup
bcrypt = Bcrypt(app)


# resources

class Home(Resource):
    def get(self):
        return {'message': 'Welcome to the Plug Share API', 'timestamp': datetime.utcnow().isoformat()}

                           
class SignIn(Resource):
    def post(self):
        username = str(request.form.get('username')).strip()
        password = request.form.get('password')
        
        user = db.users.find_one({'username': username})
        if user is None:
            return {'signin_status': False, 'message': 'User not found', 'timestamp': datetime.utcnow().isoformat()}
        if not bcrypt.check_password_hash(user.get('password'), password):
            return {'signin_status': False, 'message': 'Incorrect password', 'timestamp': datetime.utcnow().isoformat()}

        return {'signin_status': True, 'timestamp': datetime.utcnow().isoformat()}


class SignUp(Resource):
    def post(self):
        username = str(request.form.get('username')).strip()
        password = request.form.get('password')
        contact = str(request.form.get('contact')).strip()
        
        existing_user = db.users.find_one({'username': username})
        if existing_user is not None:
            return {'signup_status': False, 'message': 'Username already exists', 'timestamp': datetime.utcnow().isoformat()}
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        db.users.insert_one({'username': username, 'password': hashed_password, 'contact': contact})    
        return {'signup_status': True, 'message': 'User created successfully', 'timestamp': datetime.utcnow().isoformat()}
    

class AddPlug(Resource):
    def post(self):
        # Implementation for adding a plug
        plug = str(request.form.get('plug')).strip()
        location = str(request.form.get('location')).strip()
        user_id = request.form.get('user_id')
        status = True
        date = datetime.utcnow()
        
        result = db.plugs.insert_one({
            'plug': plug,
            'location': location,
            'user_id': user_id,
            'status': status,
            'date': date
        })

        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$addToSet': {'plugs': str(result.inserted_id)}}
        )

        return {'add_plug_status': True, 'timestamp': datetime.utcnow().isoformat()}
    
class EditPlug(Resource):
    def post(self):
        plug_id = request.form.get('plug_id')
        plug = str(request.form.get('plug')).strip()
        location = str(request.form.get('location')).strip()        

        db.plugs.update_one(
            {'_id': ObjectId(plug_id)},
            {'$set': {
                'plug': plug,        
                'location': location
            }}
        )

        return {'edit_plug_status': True, 'timestamp': datetime.utcnow().isoformat()}
    
class MyPlugs(Resource):
    def get(self):
        user_id = request.form.get('user_id')
        plugs = list(db.plugs.find({'user_id': user_id}))

        for plug in plugs:
            plug['_id'] = str(plug['_id'])
            plug['date'] = plug['date'].isoformat()
        
        return {'plugs': plugs, 'timestamp': datetime.utcnow().isoformat()}

class DeletePlug(Resource):
    def delete(self):
        plug_id = request.form.get('plug_id')
        user_id = request.form.get('user_id')
        db.plugs.delete_one({'_id': ObjectId(plug_id), 'user_id': user_id})
        
        return {'delete_plug_status': True, 'timestamp': datetime.utcnow().isoformat()}
    
class LikePlug(Resource):
    def post(self):
        plug_id = request.form.get('plug_id')
        user_id = request.form.get('user_id')

        db.plugs.update_one(
            {'_id': ObjectId(plug_id)},
            {'$pull': {'likes': {'user_id': user_id}}}
        )

        db.plugs.update_one(
            {'_id': ObjectId(plug_id)},
            {'$addToSet': {'likes': {'user_id': user_id, 'date': datetime.utcnow()}}}
        )

        db.plugs.update_one(
            {'_id': ObjectId(plug_id)},
            {'$pull': {'dislikes': {'user_id': user_id}}}
        )

        return {'like_status': True, 'timestamp': datetime.utcnow().isoformat()}


class DislikePlug(Resource):
    def post(self):
        plug_id = request.form.get('plug_id')
        user_id = request.form.get('user_id')

        db.plugs.update_one(
            {'_id': ObjectId(plug_id)},
            {'$pull': {'dislikes': {'user_id': user_id}}}
        )

        db.plugs.update_one(
            {'_id': ObjectId(plug_id)},
            {'$addToSet': {'dislikes': {'user_id': user_id, 'date': datetime.utcnow()}}}
        )

        db.plugs.update_one(
            {'_id': ObjectId(plug_id)},
            {'$pull': {'likes': {'user_id': user_id}}}
        )

        return {'dislike_status': True, 'timestamp': datetime.utcnow().isoformat()}

class GetUsers(Resource):
    def get(self):
        users = list(db.users.find())
        for user in users:
            user['_id'] = str(user['_id'])
            del user['password']
        return {'users': users, 'timestamp': datetime.utcnow().isoformat()}


api.add_resource(Home, '/')
api.add_resource(SignIn, '/signin')
api.add_resource(SignUp, '/signup')
api.add_resource(AddPlug, '/addplug')
api.add_resource(EditPlug, '/editplug')
api.add_resource(DeletePlug, '/deleteplug')
api.add_resource(MyPlugs, '/myplugs')
api.add_resource(LikePlug, '/likeplug')
api.add_resource(DislikePlug, '/dislikeplug')
api.add_resource(GetUsers, '/getusers')