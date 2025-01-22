from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField
from wtforms import BooleanField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError
#from leaderboard.models import User, Team
from wtforms.validators import Regexp
import re

def validate_qnumber(form, field):
    qnumber = field
    if int(qnumber.data) < 0:
        raise ValidationError("Select the Question Number corresponding to the uploaded solution")

def validate_edm4eic(form, field):
    filename = field.data.filename
    # Define the regex for .edm4eic*.root
    pattern = r'\.edm4eic.*\.root$'
    if not re.search(pattern, filename):
        raise ValidationError('Invalid file extension. Please upload a .edm4eic.root file.')

class SubmitForm(FlaskForm):
    username = StringField('User name', validators=[DataRequired()])
    name = StringField('Full Name', validators=[DataRequired()])
    # Currently there is only one question
    _choices = [(-1, "Select the Question")] + [(i, f'Question {i}') for i in range(1, 3)]
    qnumber = SelectField('Submitting Solution for Question',
                        choices=_choices,
                        validators=[DataRequired(), validate_qnumber],
                        default = -1
                        )
    remark = StringField('Remarks (optional)',
                        validators=[Length(min=0, max=255)]
                        )
    result_file = FileField(r"Results file (Only .edm4eic.root format)",
                            validators=[validate_edm4eic,
                                        FileRequired()
                                        ] 
                            )
    submit = SubmitField('Evaluate Results')


class SignUpForm(FlaskForm):
    username = StringField('User Name', render_kw={"placeholder": "Enter your username"},
                        validators = [DataRequired()])
    fname = StringField('First name', render_kw={"placeholder": "Enter your first name"},
                        validators=[DataRequired()])
    lname = StringField('Last name', render_kw={"placeholder": "Enter your last name"},
                        validators=[DataRequired()])
    institution = StringField('Institution', render_kw={"placeholder": "Enter your institution"},
                        validators=[DataRequired()])
    password = PasswordField('Password', render_kw={"placeholder": "Enter your password"},
                        validators=[DataRequired()])
    role = SelectField(
        'Designation',
        choices=[
        ('Student', 'Student'), 
        ('Post Doc', 'Post Doc'),
        ('Professor', 'Professor'),
        ('Researcher', 'Researcher'),
        ('Other', 'Other')
        ],
        render_kw={"placeholder": "Select your role"},
        validators=[DataRequired()]
    )
    
    submit = SubmitField('Login')
    
    def change_submitlabel(self, label):
        self.submit.label.text = label

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], render_kw={"placeholder": "Enter your username"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Enter your password"})
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

