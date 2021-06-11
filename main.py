import datetime
import json
import sys
import time
import uuid
import os
import firebase_admin
from passlib.hash import pbkdf2_sha256
from firebase_admin import credentials
from firebase_admin import db
from flask import Blueprint, render_template, abort
from google.cloud import storage
import pytz
from flask import Flask, flash, request, session, jsonify
from flask_compress import Compress
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.utils import secure_filename
from flask import redirect, url_for
from flask import render_template, send_file
from flask_session import Session
from flask_sslify import SSLify
from werkzeug.datastructures import ImmutableOrderedMultiDict
import atexit
from werkzeug.local import Local, LocalManager
from apscheduler.schedulers.background import BackgroundScheduler
import stripe
import plivo
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from inspection_engine.groups.admin import fire_admin_billing, fire_admin_panel, fire_admin_log
from inspection_engine.groups.gov import fire_gov_panel, fire_gov_form
from inspection_engine.groups.user import fire_user_panel, fire_system_testing, fire_system_registration, fire_system_amend, fire_user_login
from inspection_engine.global_modules import login, signup, main_page


stripe.api_key = "STRIPE_KEY"

sg = SendGridAPIClient(
    'SG_KEY')

bot_number = "14255992978"
service_email = 'cajohn0205@gmail.com'
service_number = '17203269719'

client = plivo.RestClient(auth_id='AUTH_ID',
                          auth_token='AUTH_TOKEN')    

infoFile = open("info.json")
info = json.load(infoFile)
global main_link
main_link = info['main_link']

storage_client = storage.Client.from_service_account_json(
    "compliancy-app-firebase-adminsdk-bd193-f9c1957881.json")
cred = credentials.Certificate(
    'compliancy-app-firebase-adminsdk-bd193-f9c1957881.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://compliancy-app.firebaseio.com/',
    'storageBucket': 'compliancy-app.appspot.com'
})


bucket = storage_client.get_bucket("compliancy-app.appspot.com")

sched = BackgroundScheduler(daemon=True)
sched.add_job(fire_admin_billing.monthly_log, 'interval', minutes=30)
sched.start()


app = Flask(__name__)
sslify = SSLify(app)
scKey = str(uuid.uuid4())
app.secret_key = scKey


app.register_blueprint(fire_admin_panel.panel_blueprint)
app.register_blueprint(fire_admin_billing.billing_blueprint)
app.register_blueprint(fire_admin_log.log_blueprint)

app.register_blueprint(fire_user_panel.panel_blueprint)
app.register_blueprint(fire_user_login.login_blueprint)
app.register_blueprint(fire_system_testing.system_test_blueprint)
app.register_blueprint(fire_system_amend.system_amend_blueprint)
app.register_blueprint(fire_system_registration.system_register_blueprint)

app.register_blueprint(fire_gov_panel.panel_blueprint)
app.register_blueprint(fire_gov_form.form_blueprint)

app.register_blueprint(login.login_blueprint)
app.register_blueprint(signup.signup_blueprint)
app.register_blueprint(main_page.main_page_blueprint)


def send_email(recipients, message_content, subject_content):
    message = Mail(
        from_email='noreply@sentintelfw.com',
        to_emails=recipients,
        subject=subject_content,
        html_content=message_content)
    try:
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)



@app.errorhandler(405)
def handler404(e):
    return (str(e), 405)


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    print(e)
    referrer = request.headers.get("Referer")
    return (redirect(referrer), 302)

    # <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>


@app.route('/<comp_name>/error-<error>')
def error(comp_name, error):
    return render_template("user/error-page.html", comp_name=comp_name, error=error)


@app.route('/contact-support', methods=['POST'])
def contact_support():
    rsp = dict(request.form)

    req_type = rsp['type']
    name = rsp['name']
    serverity = rsp['severity']
    issue = rsp['issue']
    user = rsp['user']

    if(serverity == 'green'):
        write_str = '<h3>Customer service has received your message and will be in touch with you shortly</h3><br><br>'

        write_str += "<h5>Your Message:</h5><br>" + "<br><p>" + issue + "</p>"
        subject = "Sentinel Fire Watch Support"

        send_email([user], write_str, subject)

        write_str = "<h3>Code Green</h3><br>"

        write_str += "<h5>Type:</h5><br>" + req_type + '<br>'

        write_str += "<h5>Name: " + name + '</h5><br>'

        write_str += "<h5>User: " + user + '</h5>'

        write_str += "<h5>Message:<br>" + issue + '<br>'

        subject = "Sentinel Fire Watch Support Request"

        send_email([service_email], write_str, subject)

    elif (serverity == 'yellow'):
        write_str = "<h5>Customer service has received your message and are working to reslove your issue(s) as soon as quickly as possible and will contact you shortly</h5>" + '<br>'

        write_str += "<h5>Your Message:" + '<br>' + issue + "</h5>"

        subject = "Sentinel Fire Watch Support"

        send_email([user], write_str, subject)

        write_str = "<h3>Code Yellow</h3>" + '<br>'

        write_str += "<h5>Type:" + req_type + '</h5><br>'

        write_str += "<h5>Name: " + name + '</h5><br>'

        write_str += "User:" + user + '<br>' + '<br>'

        write_str += "<h5>Message:<br>" + issue + '</h5>'

        subject = "Sentinel Fire WatchSupport Request"

        send_email([service_email], write_str, subject)
        client.messages.create(
            src=bot_number,
            dst=service_number,
            text='Code Yellow Service Request ' + req_type + " - " + name
        )

    elif (serverity == 'red'):
        write_str = "<h5>Customer Service has been alerted of your problem and will contact you as soon as possible</h5>" + '<br>' + '<br>'
        write_str += "<h6>Your Message:<br>" + issue + '</h5>'

        subject = "Sentinel Fire Watch Support"

        send_email([user], write_str, subject)

        write_str = "<h5>Code Red</h5>" + '<br>'

        write_str += "<h5>Type: " + req_type + '</h5><br>'

        write_str += "<h5>Name: " + name + '</h5><br>'

        write_str += "<h5>User: " + user + '</h5><br>'

        write_str += "<h5>Message: " + issue + '</h5><br>'

        subject = "Sentinel Fire Watch Support Request"

        send_email([service_email], write_str, subject)
        client.messages.create(
            src=bot_number,
            dst=service_number,
            text='CODE RED SERVICE REQUEST ' + req_type + " - " + name
        )

    referrer = request.headers.get("Referer")
    #return (redirect(referrer), 302)
    return render_template('alert.html', alert="Request Sent", page=referrer)


'''

@app.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

'''



Compress(app)
csrf = CSRFProtect(app)
csrf.exempt(fire_user_login.login_blueprint)
csrf.exempt(fire_user_panel.panel_blueprint)
csrf.exempt(fire_system_registration.system_register_blueprint)
csrf.exempt(fire_system_testing.system_test_blueprint)
if __name__ == '__main__':
    try:
        app.secret_key = scKey
        sslify = SSLify(app, permanent=True)
        app.config['SESSION_TYPE'] = 'filesystem'
        sess = Session()
        sess.init_app(app)
        csrf.init_app(app)
        sess.permanent = True
        app.jinja_env.cache = {}
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
    except KeyboardInterrupt:
        sys.exit()
