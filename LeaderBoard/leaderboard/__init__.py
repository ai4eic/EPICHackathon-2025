from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_session import Session
from datetime import timedelta
from flask_dance.contrib.github import make_github_blueprint, github

#from flask_bootstrap import Bootstrap5

app = Flask(__name__)

app.secret_key = "5791628bb0b13ce0c676dfde280ba245"
app.config['SECRET_KEY'] = app.secret_key
app.config["DB_NAME"] = "users.db"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config["DB_NAME"]
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
app.app_context().push()
db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

config = {
    "DEBUG": True,          # some Flask specific configs
}
app.config.from_mapping(config)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Login in using your GitHub account.'
login_manager.login_message_category = 'info'
login_manager.refresh_view = "accounts.reauthenticate"
login_manager.needs_refresh_message = (
    u"To protect your account, please reauthenticate to access this page."
)
login_manager.needs_refresh_message_category = "info"

app.config['SESSION_TYPE'] = 'filesystem'
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=6)
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_FILE_DIR"] = "flask_sessions" 
#app.config["SESSION_COOKIE_SECURE"] = True  # Use HTTPS only
#app.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevent JavaScript access
#app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # Mitigate CSRF
sess = Session(app)

## GitHub OAuth
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ["GITHUB_CLIENT_ID"] = "Ov23liReB1ryL6zeHvgr"
os.environ["GITHUB_CLIENT_SECRET"] = "5440b3fb5d2399657abf0ab8852f5694730355b7"

github_blueprint = make_github_blueprint(
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    redirect_to="login",  # Redirect to organizations route
    scope = "read:org"
)

app.register_blueprint(github_blueprint, url_prefix="/login")


UPLOAD_FOLDER = os.path.join(os.getcwd(), 'submissions')
RES_FOLDER = os.path.join(os.getcwd(), 'actual_results')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MDEDITOR_FILE_UPLOADER'] = UPLOAD_FOLDER
app.config['RES_FOLDER'] = RES_FOLDER

if(not os.path.exists(app.config['RES_FOLDER'])):
    os.makedirs(app.config['RES_FOLDER'])

if(not os.path.exists(app.config['UPLOAD_FOLDER'])):
    os.makedirs(app.config['UPLOAD_FOLDER'])

app.config["ORG_NAME"] = "eic"
from leaderboard import routes
