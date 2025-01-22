import os
from flask import render_template, url_for, flash, redirect, abort, request
from leaderboard import app, db, csrf, bcrypt
from leaderboard.forms import SignUp, SubmitForm, LoginForm
from leaderboard.models import User, Question
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from datetime import datetime
from leaderboard.evaluator import EvaluateDirc

from markupsafe import Markup
# Some default settings

from uuid import NAMESPACE_OID, uuid1, uuid5
from flask_dance.contrib.github import github

"""
    @app.errorhandler(Exception)
def handle_exception(e):
    return render_template("error_500.html", e=e), 500
"""
@app.before_request
def csrf_protect():
    if request.method in ("POST", "PUT", "DELETE"):
        csrf.protect()
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
    flash("You have been logged out!", "info")
    return redirect(request.args.get('next', url_for('leaderboard')))

@app.route("/login", methods=['GET', 'POST'])
def login():
    print ("USER AUTHENTICATED: ", current_user.is_authenticated)
    if current_user.is_authenticated:
        print ("USER AUTHENTICATED: ", current_user.username)
        if github.authorized:
            flash("You are already logged in", "info")
            return redirect(url_for("leaderboard"))
        else:
            print ("GITHUB NOT AUTHORIZED")
            return redirect(url_for("github.login"))
    else:
        return redirect(url_for("github.login"))

@app.route("/github_authorized")
def github_authorized():
    if not github.authorized:
        flash("Authentication error. Please login via GitHub", "danger")
        return redirect(url_for('index'))
    account_resp = github.get("/user")
    print ("ACCOUNT RESPONSE: ", account_resp.ok)
    if account_resp.ok:
        account_info = account_resp.json()
        git_id = account_info.get('id')
        username = account_info.get('login')
        user = User.query.get(git_id)
        if user:
            login_user(user)
            flash(f"Welcome back {user.username}", "info")
            return redirect( url_for('leaderboard') )
        else:
            return redirect(url_for('signup', uname = username))
    elif account_resp.status_code == 401:
        flash("Unauthorized access. Please login again", "danger")
        return redirect(url_for("github.login"))
    elif account_resp.status_code == 403:
        app.config["MAX_RATE_LIMIT"] = True
        flash("Forbidden access. Please login using traditional method", "danger")
        print ("MAX RATE LIMIT")
        return redirect(url_for("leaderboard"))
    elif account_resp.status_code == 429:
        app.config["MAX_RATE_LIMIT"] = True
        flash("Forbidden access. Please login using traditional method", "danger")
        print ("MAX RATE LIMIT")
        return redirect(url_for("leaderboard"))
    else:
        flash("Unable to get user information from GitHub", "danger")
        return redirect(url_for('index'))
        
@app.route("/signup/<uname>", methods=['GET', 'POST'])
def signup(uname):
    if not github.authorized:
        flash("Authentication error. Please login via GitHub", "danger")
        return redirect(url_for("github.login"))
    org_resp = github.get(f"/orgs/{app.config['ORG_NAME']}/members/{uname}")
    print ("ORG RESPONSE: ", org_resp.status_code)
    if (org_resp.status_code != 204 and not app.config['DEBUG']):
        flash("You are not a member of the EIC organization, please contact ePIC Hackathon Organizers", "danger")
        return redirect(url_for('index'))
    
    account_resp = github.get("/user")
    user_data = {}
    if account_resp.ok:
        account_info = account_resp.json()
        user_data['git_id'] = int(account_info.get('id'))
        user_data['username'] = account_info.get('login')
        user_data['name'] = account_info.get('name') or " "
        user_data['fname'] = user_data['name'].split(' ')[0]
        user_data['lname'] = ' '.join(user_data['name'].split(' ')[1:])
        user_data['git_url'] = account_info.get('html_url')
        user_data['avatar_url'] = account_info.get('avatar_url') 
    elif account_resp.status_code == 401:
        flash("Unauthorized access. Please login again", "danger")
        return redirect(url_for("github.login"))
    elif account_resp.status_code == 403:
        app.config["MAX_RATE_LIMIT"] = True
        flash("Forbidden access. Please login using traditional method", "danger")
        print ("MAX RATE LIMIT")
        return redirect(url_for("github.login"))
    elif account_resp.status_code == 429:
        app.config["MAX_RATE_LIMIT"] = True
        flash("Forbidden access. Please login using traditional method", "danger")
        print ("MAX RATE LIMIT")
        return redirect(url_for("leaderboard"))
    else:
        flash("Unable to get user information from GitHub", "danger")
        return redirect(url_for('index'))
    print ("USER DATA: ", user_data)
    _user_data = {"username": user_data['username'], "fname": user_data['fname'], "lname": user_data['lname']}
    form = SignUp(data = _user_data)
    if form.validate_on_submit():
        if not form.csrf_token.data:
            flash("CSRF token is missing or invalid. Please try again", "danger")
            return redirect(url_for('signup'))
        try:
            name = form.fname.data + " " + form.lname.data
            user = User(username = form.username.data,
                        name = name,
                        fname = form.fname.data,
                        lname = form.lname.data,
                        git_id = user_data['git_id'],
                        git_url = user_data['git_url'],
                        avatar_url = user_data['avatar_url'],
                        institution = form.institution.data,
                        role = form.role.data,
                        userHash = str(uuid5(NAMESPACE_OID, str(user_data['git_id']))),
                        overallscore = 0,
                        Nattempts = 0
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            # create user submission folder
            user_folder = os.path.join(app.config['UPLOAD_FOLDER'], user.userHash)
            if ( not os.path.exists(user_folder) ):
                os.makedirs(user_folder)
            login_user(user)
            flash(f"Account created for {form.username.data}!", "success")
            return redirect(url_for('leaderboard'))
        except Exception as e:
            print (e)
            flash(f"Account creation failed for {form.username.data}! Contact ePIC Hackathon Organizers", "danger")
            return redirect(url_for('leaderboard'))
    return render_template('signup.html', title='Sign Up', form=form)
@app.route("/traditional_login", methods=['GET', 'POST'])
def traditional_login():
    if not app.config.get("MAX_RATE_LIMIT"):
        flash("You are not allowed to login via traditional method", "danger")
        return redirect(url_for("leaderboard"))
    if current_user.is_authenticated:
        flash("You are already logged in", "info")
        return redirect(url_for("leaderboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f"Welcome back {user.username}", "info")
            return redirect(url_for('leaderboard'))
        else:
            flash("Login Unsuccessful. Please check username and password", "danger")
    return render_template("traditional_login.html", title="Login", form = form)
    

@app.route("/submit", methods=['GET', 'POST'])
@login_required
def submit():
    if not github.authorized or not current_user.is_authenticated:
        flash("You are not authorized to access this page", "danger")
        return redirect(url_for("login"))
    data = {"username": current_user.username, "name": current_user.name}
    form = SubmitForm(data = data)
    form.username.render_kw = {"disabled": "disabled"}
    form.name.render_kw = {"disabled": "disabled"}
    if form.validate_on_submit():
        # Get the user information and move the file to the secure place
        _file = form.result_file.data
        now = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        _filename = secure_filename("result_" + now + "_" + _file.filename )
        
        qnumber = int(form.qnumber.data)
        res_q = app.config["Ques_Map"][qnumber]
        res_file = os.path.join(app.config["RES_FOLDER"], res_q, f"{res_q}.edm4eic.root")
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.userHash, f'{qnumber}')
        if(not os.path.exists(user_folder)):
            os.makedirs(user_folder)
        filepath = os.path.join(user_folder, _filename)
        _file.save(filepath)
        # Evaluate the file
        print (res_file, filepath)
        score, exe_err = EvaluateDirc(filepath, res_file)
        if exe_err:
            flash(f"Error in executing the evaluation script: {exe_err}", "danger")
            return redirect(url_for('submit'))
        print (score)
        
    return render_template("submit.html", title="Submit your solutions", form = form)

