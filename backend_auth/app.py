import os
import sys

from authService import authService 
from dbdef import db
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

idp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, idp_dir)

app = Flask(__name__)

db_user = os.environ.get("DB_USER", "apple")
db_password = os.environ.get("DB_PASSWORD", "0000")
db_host = os.environ.get("DB_HOST", "localhost")
db_port = os.environ.get("DB_PORT", "5432")
db_name = os.environ.get("DB_NAME", "trip_connect")

db_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

SECRET_KEY = os.environ.get('SECRET_KEY')
app.config['SECRET_KEY'] = SECRET_KEY

db.init_app(app)
app.register_blueprint(authService)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=6001)

