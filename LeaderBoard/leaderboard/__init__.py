from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from datetime import timedelta
from flask_dance.contrib.github import make_github_blueprint
from flask_wtf.csrf import CSRFProtect
#from flask_session import Session

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", None)
app.config['SECRET_KEY'] = app.secret_key

# CSRF Protection
# Initialize CSRF protection
csrf = CSRFProtect(app)

app.config["DB_DIR"] = os.environ.get("DB_DIR", os.getcwd()) #os.path.join(os.getcwd(), "db")
if not os.path.exists(app.config["DB_DIR"]):
    os.makedirs(app.config["DB_DIR"])
app.config["DB_NAME"] = os.environ.get("DB_NAME") #"users.db"
app.config["DB_PATH"] = os.path.join(app.config["DB_DIR"], app.config["DB_NAME"])
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config["DB_PATH"]
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False # True to track modifications but memory intensive

app.app_context().push() # Push the application context to create the database
db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

config = {
    "DEBUG": os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")          # some Flask specific configs
}
app.config.from_mapping(config)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Login in using your GitHub account.'
login_manager.login_message_category = 'info'
login_manager.refresh_view = "login"
login_manager.needs_refresh_message = (
    u"To protect your account, please reauthenticate to access this page."
)
login_manager.needs_refresh_message_category = "info"

login_manager.session_protection = "strong"


# IF you want to store the session in the filesystem 
# (Session data could be shared between different instances of the app)
# app.config['SESSION_TYPE'] = 'filesystem' 

# # If you want to store the session in the database
# app.config["SESSION_PERMANENT"] = True
# # Set the lifetime of the session
# app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=4) # 4 hours
# app.config["SESSION_USE_SIGNER"] = True # Sign the session cookie
# #app.config["SESSION_FILE_DIR"] = "flask_sessions"  # Directory to store session files
# app.config["SESSION_COOKIE_SECURE"] = True  # Use HTTPS only
# app.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevent JavaScript access
# app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # Mitigate CSRF
# app.config["SESSION_COOKIE_NAME"] = "ePIC_Hackathon_2025"  # Custom cookie name
# sess = Session(app)

# Make sure to have GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in the environment
github_blueprint = make_github_blueprint(
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    redirect_to="github_authorized",  # Redirect to organizations route
    scope = "read:org"
)

app.register_blueprint(github_blueprint, url_prefix="/login")

if not os.environ.get("UPLOAD_FOLDER"):
    os.environ["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), 'submissions')
app.config['UPLOAD_FOLDER'] = os.environ.get("UPLOAD_FOLDER")

if(not os.path.exists(app.config['UPLOAD_FOLDER'])):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.environ.get("RES_FOLDER"):
    raise FileNotFoundError(f"Results folder {app.config['RES_FOLDER']} does not exist. Please check the path")
app.config["RES_FOLDER"] = os.environ.get("RES_FOLDER")
app.config["Ques_Map"] = {
    1: "DIRC"
}
# check if the folder and file exists for each of Question
for key, value in app.config["Ques_Map"].items():
    if not os.path.exists(app.config['RES_FOLDER'] + f"/{value}/{value}.edm4eic.root"):
        print (app.config['RES_FOLDER'] + f"/{value}/{value}.edm4eic.root")
        raise FileNotFoundError(f"Results file {app.config['RES_FOLDER']}/{value}/{value}.edm4eic.root does not exist. Please check the path")

app.config["ORG_NAME"] = os.environ.get("ORG_NAME", "eic")
app.config["MAX_RATE_LIMIT"] = True

from leaderboard import routes


