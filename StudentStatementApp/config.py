from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_url_path="/static")
app.name = "StudentStatementApp"
app.debug = True
app.config["SECRET_KEY"] = "\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR'\xa1\xa8"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
UPLOAD_FOLDER = f"./{app.static_url_path}/upload/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
database = SQLAlchemy(app)
