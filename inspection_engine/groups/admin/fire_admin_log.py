from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name
from import_modules import *
import threading
import queue

storage_client = storage.Client.from_service_account_json(
    "compliancy-app-firebase-adminsdk-bd193-f9c1957881.json")
bucket = storage_client.get_bucket("compliancy-app.appspot.com")

log_blueprint = Blueprint(
    'fire_admin_log', __name__, template_folder='templates')


def check_user_token(user, token):
    try:
        path_user = "/users/" + user
        user_data = dict(db.reference(path_user).get())
        if ((user_data["token"] == token) and (time.time() - user_data["time"] < 3600)):
            db.reference(path_user).update({"time": time.time()})
            return 0
        else:
            return 1
    except Exception as e:
        print(e, 'err')
        return 1





@log_blueprint.route('/<comp_name>/past-reg-data')
def past_reg_data(comp_name):
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))

    log_ref = db.reference('/companies/' + comp_name + '/log')
    logs = dict(log_ref.get())

    log_keys = []

    time_keys = []

    for k,v in logs.items():
        time_keys.append(v['time'])

    time_keys.sort()
    time_keys = time_keys[::-1]

    print(time_keys)

    for time_key in time_keys:
        print(time_key)
        for k,v in logs.items():
            print(v, time_key)
            if(v['time'] == time_key):
                log_keys.append(k)


    return render_template('admin/past-reg-data.html', logs=logs, log_keys=log_keys)



@log_blueprint.route('/<comp_name>/past-report-data')
def past_report_data(comp_name):
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))

    log_ref = db.reference('/companies/' + comp_name + '/log')
    logs = dict(log_ref.get())

    log_keys = []

    time_keys = []

    for k,v in logs.items():
        time_keys.append(v['time'])

    time_keys.sort()
    time_keys = time_keys[::-1]

    print(time_keys)

    for time_key in time_keys:
        print(time_key)
        for k,v in logs.items():
            print(v, time_key)
            if(v['time'] == time_key):
                log_keys.append(k)


    return render_template('admin/past-report-data.html', logs=logs, log_keys=log_keys)



@log_blueprint.route('/<comp_name>/past-tag-data')
def past_tag_data(comp_name):
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))

    log_ref = db.reference('/companies/' + comp_name + '/log')
    logs = dict(log_ref.get())

    log_keys = []

    time_keys = []

    for k,v in logs.items():
        time_keys.append(v['time'])

    time_keys.sort()
    time_keys = time_keys[::-1]

    print(time_keys)

    for time_key in time_keys:
        print(time_key)
        for k,v in logs.items():
            print(v, time_key)
            if(v['time'] == time_key):
                log_keys.append(k)

    return render_template('admin/past-tag-data.html', logs=logs, log_keys=log_keys)




@log_blueprint.route('/<comp_name>/past-tech-reg-data')
def past_tech_reg_data(comp_name):
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))

    log_ref = db.reference('/companies/' + comp_name + '/log')
    logs = dict(log_ref.get())

    log_keys = []

    time_keys = []

    for k,v in logs.items():
        time_keys.append(v['time'])

    time_keys.sort()
    time_keys = time_keys[::-1]

    print(time_keys)

    for time_key in time_keys:
        print(time_key)
        for k,v in logs.items():
            print(v, time_key)
            if(v['time'] == time_key):
                log_keys.append(k)

    return render_template('admin/past-tech-reg-data.html', logs=logs, log_keys=log_keys)


@log_blueprint.route('/<comp_name>/past-tech-report-data')
def past_tech_report_data(comp_name):
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))

    log_ref = db.reference('/companies/' + comp_name + '/log')
    logs = dict(log_ref.get())

    log_keys = []

    time_keys = []

    for k,v in logs.items():
        time_keys.append(v['time'])

    time_keys.sort()
    time_keys = time_keys[::-1]

    print(time_keys)

    for time_key in time_keys:
        print(time_key)
        for k,v in logs.items():
            print(v, time_key)
            if(v['time'] == time_key):
                log_keys.append(k)

    return render_template('admin/past-tech-report-data.html', logs=logs, log_keys=log_keys)