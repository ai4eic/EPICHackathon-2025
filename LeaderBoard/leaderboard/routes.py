import os
from flask import render_template, url_for, flash, redirect, abort, request, jsonify, session
from flask import abort
from leaderboard import app, db, bcrypt
from leaderboard.forms import SignUp, SubmitForm
from leaderboard.models import User, Question
from flask_login import login_user, current_user, logout_user, login_required, user_needs_refresh
from werkzeug.utils import secure_filename
from datetime import datetime
from leaderboard.evaluator import Evaluate
import logging
from markupsafe import Markup
# Some default settings

from uuid import NAMESPACE_OID, uuid1, uuid5
from flask_dance.contrib.github import github

"""
    @app.errorhandler(Exception)
def handle_exception(e):
    return render_template("error_500.html", e=e), 500
"""
@app.errorhandler(404)
def page_not_found(e):
    return render_template('page_not_found.html'), 404

@app.errorhandler(403)
def access_forbidden(e):
    return render_template('acess_denied.html'), 403
@app.errorhandler(400)
def bad_request(e):
    return render_template('error_500.html'), 400
@app.route("/")
@app.route("/leaderboard")
def leaderboard():
    print (User.query.all())
    UserInfo = User.query.order_by(User.overallscore.desc()).all()
    return render_template('leaderboard.html', userinfo = UserInfo)


@app.route("/allusers")
def allusers():
    return render_template('error_500.html')

@app.route("/recent_submissions")
@login_required
def recent_submissions():
    return render_template('error_500.html')
@app.route("/logout")
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out!", "info")
    return redirect(request.args.get('next', url_for('leaderboard')))

@app.route("/login", methods=['GET', 'POST'])
def login():
    print ("Session if is ", session.get("id"))
    print ("USER AUTHENTICATED: ", current_user.is_authenticated)  
    if not github.authorized and not current_user.is_authenticated:
        return redirect(url_for("github.login"))
    _oauth = session.get("github_oauth_token")
    print (f"github info is : {_oauth} and {github.authorized}")
    print ("Session UUID is : ", session.get("userUUID"))
    if session.get("userUUID"):
        print ("User UUID is : ", session["userUUID"])
        user = User.query.filter_by(userHash = str(session["userUUID"])).first()
        if user:
            login_user(user)
            flash(f"Welcome back {user.username}", "info")
            session["userUUID"] = user.userHash
            session["username"] = user.username
            session["uid"] = user.git_id
            session["name"] = user.name
            session["git_url"] = user.git_url
            session["avatar_url"] = user.avatar_url
            return redirect(request.args.get('next', url_for('leaderboard')))
        else:
            return redirect(url_for('signup', val = 1))
    else:
        account_resp = github.get("/user")
        if account_resp.ok:
            rates = github.get("/rate_limit")
            print ("rates: ", rates.json())
            account_info = account_resp.json()
            uname = account_info.get('login')
            uid = account_info.get('id')
            userUUID = uuid5(NAMESPACE_OID, f"{uid}")
            session["userUUID"] = userUUID
            session["username"] = uname
            session["uid"] = uid
            session["name"] = account_info.get('name')
            session["git_url"] = account_info.get('html_url')
            session["avatar_url"] = account_info.get('avatar_url')
            user = User.query.filter_by(userHash = str(userUUID)).first()
            if user:
                login_user(user)
                flash(f"Welcome back {user.username}", "info")
                session["userUUID"] = user.userHash
                session["username"] = user.username
                session["uid"] = user.git_id
                session["name"] = user.name
                session["git_url"] = user.git_url
                session["avatar_url"] = user.avatar_url
                return redirect(request.args.get('next', url_for('leaderboard')))
            else:
                return redirect(url_for('signup', val = 0))

@app.route("/signup/<val>", methods=['GET', 'POST'])
def signup(val): 
    if not github.authorized:
        print ("This is something wrong")
        return render_template('somethingwrong_contact.html')
    user_info = dict()
    disable_form = False
    val = int(val)
    if (val == 0):
        # Get user information from the github
        account_resp = github.get("/user")
        if account_resp.ok:
            account_info = account_resp.json()
            print (f"account info : {account_info}")
            uname = account_info.get('login')
            uid = account_info.get('id')
            userUUID = uuid5(NAMESPACE_OID, f"{uid}")
            name = account_info.get('name')
            if not name:
                name = 'FirstName LastName'
            user_info = {
                "username": uname,
                "fname": name.split(' ')[0],
                "lname": name.split(' ')[1],
            }
            session["userUUID"] = userUUID
            session["username"] = uname
            session["uid"] = uid
            session["name"] = name
            session["git_url"] = account_info.get('html_url')
            session["avatar_url"] = account_info.get('avatar_url')
    elif (val == 1):
        user_info = {
            "username": session["username"],
            "fname": session["name"].split(' ')[0],
            "lname": session["name"].split(' ')[1],
        }
    else:
        return render_template('somethingwrong_contact.html')
    org_status = github.get(f"/orgs/{app.config['ORG_NAME']}/members/{user_info['username']}")
    print ("Status code is : ", org_status.status_code)
    if (int(org_status.status_code) != 204 and not app.config['DEBUG']):
        flash("You are not a member of the EIC organization, please contact ePIC Hackathon Organizers", "danger")
        disable_form = True
    form = SignUp(data = user_info)
    if disable_form:
        form.username.render_kw = {"disabled": "disabled"}
        form.fname.render_kw = {"disabled": "disabled"}
        form.lname.render_kw = {"disabled": "disabled"}
        form.institution.render_kw = {"disabled": "disabled"}
        form.role.render_kw = {"disabled": "disabled"}
        form.submit.render_kw = {"disabled": "disabled"}
    else:
        pass
    if form.validate_on_submit():
        try:
            user = User(username = form.username.data, 
                        name = f"{form.fname.data} {form.lname.data}",
                        git_id = session["uid"],
                        git_url = session["git_url"],
                        avatar_url = session["avatar_url"],
                        institution = form.institution.data,
                        userHash = str(session["userUUID"]),
                        overallscore = 0,
                        Nattempts = 0
            )
            session["username"] = user.username
            session["name"] = user.name
            session["uid"] = session["uid"]
            session["userUUID"] = user.userHash
            session["git_url"] = user.git_url
            session["avatar_url"] = user.avatar_url
            
            db.session.add(user)
            db.session.commit()
            login_user(user)
            
            # creator the user upload folder
            user_folder = os.path.join(app.config['UPLOAD_FOLDER'], user.userHash)
            if(not os.path.exists(user_folder)):
                os.makedirs(user_folder)
            flash(f"Account created for {form.username.data}!", "success")
            return redirect(url_for('leaderboard'))
        except Exception as e:
            print (e)
            flash(f"Account creation failed for {form.username.data}! Contact ePIC Hackathon Organizers", "danger")
    #print ("Geo location : ", request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
    return render_template('signup.html', title='Sign Up', form=form)

@app.route("/submit", methods=['GET', 'POST'])
@login_required
def submit():
    if not github.authorized and not current_user.is_authenticated:
        return redirect(url_for("login"))
    uname = session.get("username")
    name = session.get("name")
    userUUID = session.get("userUUID")
    user = User.query.filter_by(userHash = userUUID).first()
    disable_form = False
    if not user or not userUUID:
        flash("Please login/re-login to submit your solutions", "danger")
        disable_form = True
    data = {"username": uname, "name": name}
    form = SubmitForm(data = data)
    if disable_form:
        form.username.render_kw = {"disabled": "disabled"}
        form.name.render_kw = {"disabled": "disabled"}
        form.qnumber.render_kw = {"disabled": "disabled"}
        form.result_file.render_kw = {"disabled": "disabled"}
        form.submit.render_kw = {"disabled": "disabled"}
    form.username.render_kw = {"disabled": "disabled"}
    form.name.render_kw = {"disabled": "disabled"}
    
    if form.validate_on_submit():
        # Get the user information and move the file to the secure place
        _file = form.result_file.data
        now = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        _filename = secure_filename("result_" + now + "_" + _file.filename )
        
        qnumber = int(form.qnumber.data)
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], user.userHash, f'{qnumber}')
        if(not os.path.exists(user_folder)):
            os.makedirs(user_folder)
        filepath = os.path.join(user_folder, _filename)
        _file.save(filepath)
        
        
    return render_template("submit.html", title="Submit your solutions", form = form)

