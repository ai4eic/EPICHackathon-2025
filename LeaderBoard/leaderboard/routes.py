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
    session.clear()
    logout_user()
    flash("You have been logged out!", "info")
    return redirect(request.args.get('next', url_for('leaderboard')))

@app.route("/login", methods=['GET', 'POST'])
def login():
    print ("Session ID: ", session.get("_id"))
    print ("USER AUTHENTICATED: ", current_user.is_authenticated)  
    if not github.authorized and not current_user.is_authenticated:
        return redirect(url_for("github.login"))
    if current_user.is_authenticated:
        return redirect(url_for('leaderboard'))
    account_resp = github.get("/user")
    if account_resp.ok:
        account_info = account_resp.json()
        git_id = account_info.get('id')
        username = account_info.get('login')
        user_hash = uuid5(NAMESPACE_OID, f"{git_id}")
        user = User.query.filter_by(userHash = str(user_hash)).first()
        if not user:
            session.update({
                "userUUID": user_hash,
                "username": username,
                "uid": git_id,
                "name": account_info.get('name') or "FirstName LastName",
                "git_url": account_info.get('html_url'),
                "avatar_url": account_info.get('avatar_url')
                
            })
            flash("Github Authenticated !! Please complete your sign-up information.", "info")
            return redirect(url_for('signup'))
        login_user(user)
        flash(f"Welcome back {user.username}", "info")
        return redirect(request.args.get('next', url_for('leaderboard')))
    elif account_resp.status_code == 403:
        flash("GitHub API rate limit exceeded, please try again later", "danger")
        return redirect(url_for('index'))
    elif account_resp.status_code == 401:
        flash("Github Authentication failed", "danger")
        return redirect(url_for('index'))
    else:
        flash("Unexpected error occurred, please try again later", "danger")
        return redirect(url_for('index'))

@app.route("/signup", methods=['GET', 'POST'])
def signup(): 
    if not github.authorized:
        flash("Authentication error. Please login via GitHub", "danger")
        message = """
        Unable to authenticate with GitHub. 
        Please try logging in again or contact support if the issue persists.
        """
        render_template("somethingwrong_contact.html", message=message)
    user_info = {}
    disable_form = False
    account_resp = github.get("/user")
    if account_resp.ok:
        account_info = account_resp.json()
        name = account_info.get('name') or "FirstName LastName"
        user_info = {
            "username": account_info.get('login'),
            "fname": name.split(' ')[0],
            "lname": name.split(' ')[1],
        }
        session["userUUID"] = uuid5(NAMESPACE_OID, f"{account_info.get('id')}") # store only UUID
        session["username"] = account_info.get('login')
        session["name"] = name
        session["uid"] = account_info.get('id')
        session["git_url"] = account_info.get('html_url')
        session["avatar_url"] = account_info.get('avatar_url')
    else:
        flash("Unable to get user information from GitHub", "danger")
        return redirect(url_for('index'))
    print ("Getting organizational information for User info: ", user_info)
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
    
    if form.validate_on_submit():
        if not form.csrf_token.data:
            session.clear()
            flash("CSRF token is missing or invalid. Please try again", "danger")
            return redirect(url_for('signup'))
        name = f"{form.fname.data} {form.lname.data}"
        session["name"] = name
        try:
            user = User(username = form.username.data,
                        name = name,
                        git_id = session["uid"],
                        git_url = session["git_url"],
                        avatar_url = session["avatar_url"],
                        institution = form.institution.data,
                        userHash = str(session["userUUID"]),
                        overallscore = 0,
                        Nattempts = 0
            )
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
            print ("ISSUE WITH CREATION OF ACCOUNT ", e)
            print ("ALL SESSION DATA: ", session)
            session.clear()
            flash(f"Account creation failed for {form.username.data}! Contact ePIC Hackathon Organizers", "danger")
            return redirect(url_for('leaderboard'))
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

