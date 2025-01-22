from datetime import datetime
from leaderboard import db, login_manager, bcrypt
from flask_login import UserMixin
import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    git_id = db.Column(db.Integer,
                       primary_key=True
                       )
    #id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), 
                         unique=True, 
                         nullable=False
                         )
    fname = db.Column(db.String(60),
                        unique=False,
                        nullable=False
                        )
    lname = db.Column(db.String(60),
                        unique=False,
                        nullable=False
                        )
    
    name = db.Column(db.String(60),
                     unique=False,
                     nullable=False
                    )
    
    git_url = db.Column(db.String(120),
                        unique=True,
                        nullable=False
                        )
    avatar_url = db.Column(db.String(120),
                           unique = True,
                           nullable = False
                           )
    institution = db.Column(db.String(120),
                            unique=False,
                            nullable=False
                            )
    role = db.Column(db.String(60),
                        unique=False,
                        nullable=False
    )
    password = db.Column(db.String(128),
                         unique=False,
                         nullable=False
    )
    userHash = db.Column(db.String(60),
                            unique=True,
                            nullable=False
                            )
    questions = db.relationship('Question',
                                backref = 'Q_USER_NAME',
                                lazy = True
                                )
    overallscore = db.Column(db.Float,
                            unique = False,
                            nullable = False,
                            default = 0
                            )
    Nattempts = db.Column(db.Integer,
                            unique = False,
                            nullable = False,
                            default = 0
                            )
    def get_id(self):
        """Return the git_id to satisfy Flask-Login's requirements."""
        return (self.git_id)
    def __repr__(self):
        return f"User('{self.username}')"
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)
class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key = True)
    userUUID = db.Column(db.String(60), 
                         db.ForeignKey('user.userHash'),
                         nullable = False
                         )
    qnumber = db.Column(db.Integer, nullable = False)
    qscore = db.Column(db.Float, unique = False, nullable = False)
    filename = db.Column(db.String(200), nullable = False)
    submit_time = db.Column(db.DateTime, 
                            nullable = False, 
                            default = datetime.datetime.utcnow
                            )
    remarks = db.Column(db.String(300), nullable = False, default = "")
    eval_remarks = db.Column(db.String(300), nullable = False, default = "")

    def __repr__(self):
        return f"Question('{self.userUUID}', {self.qnumber}, {self.qscore}, {self.submit_time})"
