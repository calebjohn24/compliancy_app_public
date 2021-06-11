from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name, check_fire_zone
from import_modules import *
import plivo

client = plivo.RestClient(auth_id='AUTH_ID',
                          auth_token='AUTH_TOKEN')

bot_number = "14255992978"
storage_client = storage.Client.from_service_account_json(
    "compliancy-app-firebase-adminsdk-bd193-f9c1957881.json")
bucket = storage_client.get_bucket("compliancy-app.appspot.com")


login_blueprint = Blueprint(
    'fire_gov_login', __name__, template_folder='templates')


@login_blueprint.route('/fire-admin/<zone>')
@login_blueprint.route('/fire-admin/<zone>/')
@login_blueprint.route('/fire-admin/<zone>/login', methods=['GET'])
def login(zone):
    try:
        zones = db.reference('/jurisdictions/'+zone)
        if(zones.get() != None):
            return(render_template('gov/login.html', zone=zone))
        else:
            abort(404)
    except Exception as e:
        print(e)
        abort(404)


@login_blueprint.route('/fire-admin/<zone>/login', methods=['POST'])
def login_check(zone):
    request.parameter_storage_class = ImmutableOrderedMultiDict
    rsp = dict((request.form))
    try:
        email = str(rsp['email']).replace('.', '-')
        pw = rsp['pw']
        account = db.reference('/jurisdictions/' + zone + '/accounts/' + email)
        if(account.get() != None):
            account_info = account.get()
            pass_hash = account_info['pw']
            pass_check = pbkdf2_sha256.verify(pw, pass_hash)
            print(pass_check)
            token = str(uuid.uuid4())
            if(pass_check == True):
                db.reference('/jurisdictions/' + zone + "/accounts/" + email).update({
                    "time": time.time(),
                    "token": token
                })
                session['fire-user'] = email
                session['fire-token'] = token
                session['fire-name'] = account_info['name']
                session['click'] = 'None'
                # return('logged in',200)
                return(redirect(url_for('fire_gov_panel.panel', zone=zone)))
            else:
                return(redirect(url_for('fire_gov_login.login_redo', zone=zone)))
        else:
            return(redirect(url_for('fire_gov_login.login_redo', zone=zone)))
    except Exception as e:
        print(e)
        abort(500)


@login_blueprint.route('/fire-admin/<zone>/login2', methods=['GET'])
def login_redo(zone):
    try:
        zones = db.reference('/jurisdictions/'+zone)
        if(zones.get() != None):
            return(render_template('gov/login2.html', zone=zone))
        else:
            abort(404)
    except Exception as e:
        print(e)
        abort(404)


@login_blueprint.route('/fire-admin/<zone>/pw_reset', methods=['POST'])
def reset_pw(zone):
    rsp = dict(request.form)
    reset_user = str(rsp['email']).replace(".", "-")
    number = str(db.reference(
        '/jurisdictions/'+zone+'/accounts/' + reset_user + '/number').get())
    number = '1' + number
    token = str(random.randint(100000, 999999))
    hash_val = pbkdf2_sha256.hash(token)
    db.reference('/jurisdictions/'+zone+'/accounts/' +
                 reset_user).update({'token': hash_val})
    try:
        message_created = client.messages.create(
            src=bot_number,
            dst=number,
            text='Your Inspection Engine Auth Code Is: ' + token
        )
        return render_template("gov/2fa.html", number=number[-4:], email=reset_user)
    except Exception as e:
        print(e, 'error')
        return render_template("gov/2fa.html", number='invalid')


@login_blueprint.route('/fire-admin/<zone>/check-2fa', methods=['POST'])
def check_2fa(zone):
    rsp = dict(request.form)
    email = rsp['email']
    code = rsp['code']
    user = dict(db.reference('/jurisdictions/' +
                             zone + '/accounts/' + email).get())
    if ((pbkdf2_sha256.verify(code, user['token'])) == True):
        token = str(uuid.uuid4())
        db.reference('/jurisdictions/'+zone+'/accounts/' +
                     email).update({'token': token})
        main_link = get_main_link()
        link = main_link + 'fire-admin/' + zone + \
            "/reset-pw/" + token + "/" + str(email)
        write_str = '<h4>Click <a href="' + link + '"></a> To Reset Your Password'
        subject = "Password Reset for " + \
            str(zone) + " Admin Account"
        send_user = str(email)
        send_email([send_user], write_str, subject)
        return render_template("admin/pw_reset.html")
    else:
        return render_template("msg.html", page='login', type='danger', alert="Incorrect Auth Code")


@login_blueprint.route('/fire-admin/<zone>/reset-pw/<token>/<email>')
def change_pw(zone, token, email):

    try:
        user = dict(db.reference('/jurisdictions/' +
                                 zone + '/accounts/' + email).get())
        if(user['token'] == token):
            new_token = str(uuid.uuid4())
            db.reference('/jurisdictions/' + zone + '/accounts/' +
                         email).update({'token': new_token})
            return render_template('gov/change_pw.html', zone=zone, email=email)
        else:
            return(redirect(url_for('login.login')))
    except Exception as e:
        print(e, 'error')
        return(redirect(url_for('login.login')))


@login_blueprint.route('/fire-admin/<zone>/change-pw', methods=['POST'])
def confirm_pw(zone):
    rsp = dict(request.form)
    email = rsp['user']
    pw = rsp['password']
    hash_pw = pbkdf2_sha256.hash(pw)
    db.reference('/jurisdictions/' + zone + '/accounts/' + email).update({
        'pw': hash_pw,
        'time': time.time()
    })
    user = dict(db.reference('/jurisdictions/' +
                             zone + '/accounts/' + email).get())
    session['fire-user'] = email
    session['fire-token'] = user['token']
    session['fire-name'] = user['name']
    session['click'] = 'None'
    return(redirect(url_for('fire_gov_panel.panel', zone=zone)))
