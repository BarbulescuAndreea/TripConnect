import crypt
import jwt
import os
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from werkzeug.security import check_password_hash, generate_password_hash
from flask import jsonify, request, Blueprint, Response
from datetime import datetime
from dbdef import db, Users

SECRET_KEY = os.environ.get('SECRET_KEY')

c_home = Counter('counter_for_home', 'This is my counter for /home')
c_register = Counter('counter_for_register', 'This is my counter for /users/add_user')
c_login = Counter('counter_for_login', 'This is my counter for /users/login')
c_check = Counter('counter_for_check', 'This is my counter for /users/check_user')
c_delete = Counter('counter_for_delete', 'This is my counter for /users/delete')

authService = Blueprint('authService', __name__)
salt = crypt.mksalt()

@authService.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@authService.route('/users/add_user', methods=['POST'])
def add_user():
    user_data = request.json

    if 'username' not in user_data or 'password' not in user_data:
        return jsonify({'error': 'Missing username or password'}), 400

    hashed_password = generate_password_hash(user_data['password'])

    user = Users(name=user_data['username'],
                 password=hashed_password,
                 registration_date=datetime.utcnow(),
                 email=user_data['email'])
    
    db.session.add(user)
    db.session.commit()

    c_register.inc()
    
    return jsonify({'message': 'User added successfully'}), 201

@authService.route('/users/check_user', methods=['GET'])
def check_user():
    c_check.inc()
    user_data = request.json

    if 'username' not in user_data or 'password' not in user_data:
        return jsonify({'errorMessage': 'Missing username or password'}), 400

    username = user_data['username']
    password = user_data['password']

    user = Users.query.filter_by(name=username).first()

    if user and check_password_hash(user.password, password):
        user_data = {
            'id': user.user_id,
            'name': user.name,
            'registration_date': user.registration_date,
            'email': user.email
        }
        return jsonify({'user data': user_data}), 200
    else:
        return jsonify({'error':'User Not Found'}), 401


@authService.route("/home")
def home():
    c_home.inc()
    return "Hello WORLD!"


def get_by_email(email):
    user = Users.query.filter_by(email=email).first()
    if not user:
        return
    return user

def login_real(email, password):
   user = get_by_email(email)
   if not user or not check_password_hash(user.password, password):
      return
   return user

@authService.route("/users/login", methods=["POST"])
def login():
    c_login.inc()
    try:
        data = request.get_json(silent=True)
        if not data:
            return {
                "message": "Please provide user details",
                "data": None,
                "error": "Bad request"
            }, 400
        user = login_real(data["email"], data["password"])
        if user:
            try:
                token = jwt.encode(
                    {"user_id": user.user_id},
                    SECRET_KEY,
                    algorithm="HS256"
                )
                return {
                    "message": "Successfully fetched auth token",
                    "token": token
                }
            except Exception as e:
                return {
                    "error": "Something went wrong 2",
                    "message": str(e)
                }, 500
        return {
            "message": "Error fetching auth token!, invalid email or password",
            "data": None,
            "error": "Unauthorized"
        }, 404
    except Exception as e:
        return {
                "message": "Something went wrong!",
                "error": str(e),
                "data": None
        }, 500

@authService.route("/users/delete", methods=["DELETE"])
def delete_user():
    c_delete.inc()
    try:
        user_id = request.json.get('user_id')

        if user_id is None:
            return jsonify({"error": "User ID is required in the request body"}), 400
        
        user = Users.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404
        
        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": "An error occurred while deleting the user", "details": str(e)}), 500