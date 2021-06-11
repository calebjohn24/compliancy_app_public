from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name
from import_modules import *
import plivo

login_blueprint = Blueprint(
    'login', __name__, template_folder='templates')

client = plivo.RestClient(auth_id='AUTH_ID',
                          auth_token='AUTH_TOKEN')

bot_number = "14255992978"


@login_blueprint.route('/login')
def login():
    return(render_template('login/login-new.html'))


@login_blueprint.route('/reset-pw-start')
def reset_pw_start():
    return(render_template('login/pw_reset_start.html'))

@login_blueprint.route('/login-check', methods=['POST'])
def check_login():
    rsp = dict(request.form)
    email = rsp['email']
    pw = rsp['pw']
    db_email = dict(db.reference(
        '/users').order_by_child('email').equal_to(email).get())
    if (db_email == {}):
        return (render_template('login/login2-new.html'))
    if (len(db_email) == 1):
        for key in db_email:
            pw_hash = db_email[key]['pw']
            pass_check = pbkdf2_sha256.verify(pw, pw_hash)
            if (pass_check == True):
                acct_type = db_email[key]['type']
                token = str(uuid.uuid4())
                if (acct_type == 'admin'):
                    db.reference('/users/' + key).update({
                        "time": time.time(),
                        "token": token
                    })
                    session['id'] = key
                    session['token'] = token
                    session['email'] = email
                    session['name'] = db_email[key]['name']
                    session['click'] = 'None'
                    return(redirect(url_for('fire_admin_panel.admin_panel', comp_name=db_email[key]['comp'])))
                elif (acct_type == 'tech'):
                    db.reference('/users/' + key).update({
                        "time": time.time(),
                        "token": token
                    })
                    session['id'] = key
                    session['token'] = token
                    session['email'] = email
                    session['name'] = db_email[key]['name']
                    session['click'] = 'None'
                    return render_template("msg.html", page='/', type='primary', alert="Please Login Using The Mobile App")
                elif (acct_type == 'fire-admin'):
                    db.reference('/users/' + key).update({
                        "time": time.time(),
                        "token": token
                    })
                    session['id'] = key
                    session['token'] = token
                    session['email'] = email
                    session['name'] = db_email[key]['name']
                    session['click'] = 'None'
                    # return('logged in',200)
                    return(redirect(url_for('fire_gov_panel.panel', zone=db_email[key]['zone'])))
            else:
                return (render_template('login/login2-new.html'))

    elif (len(db_email) == 2):
        for key in db_email:
            pw_hash = db_email[key]['pw']
            pass_check = pbkdf2_sha256.verify(pw, pw_hash)
            if (pass_check == True):
                token = str(uuid.uuid4())
                session['id'] = key
                session['token'] = token
                session['email'] = email
                session['name'] = db_email[key]['name']
                session['click'] = 'None'
                db.reference('/users/' + key).update({
                    "time": time.time(),
                    "token": token
                })
                return (render_template('login/pick-acct.html', comp_name=db_email[key]['comp']))
        return (render_template('login/login2-new.html'))
    # pass_check = pbkdf2_sha256.verify(pw, pass_hash)
    # token = str(uuid.uuid4())
    else:
        return (render_template('login/login2-new.html'))



@login_blueprint.route('/admin-2fa', methods=['POST'])
def send_2fa():
    rsp = dict((request.form))
    db_user = dict(db.reference(
        '/users').order_by_child('email').equal_to(str(rsp['email'])).get())
    print(db_user)
    user_key = list(db_user.keys())[0]
    print(user_key)
    user_ref = db.reference('/users/' + user_key)
    try:
        token = str(random.randint(100000, 999999))
        number = '1' + db_user[user_key]['phone']
        hash_val = pbkdf2_sha256.hash(token)
        user_ref.update({'token': hash_val})
        try:
            client.messages.create(
                src=bot_number,
                dst=number,
                text='Your Inspection Engine Auth Code Is: ' + token
            )
            
            print(token)
            return render_template("login/2fa.html", number=number[-4:], email=db_user[user_key]['email'], key=user_key)
        except Exception as e:
            print(e, 'error')
            return render_template("login/2fa.html", number='invalid')
    except Exception as e:
        print(e, 'error')
        return render_template("msg.html", page='/login', type='danger', alert="Account Does Not Exist")


@login_blueprint.route('/admin_pw_reset', methods=['POST'])
def admin_pw_reset():
    rsp = dict((request.form))
    user_key = rsp['key']
    email = str(rsp['email'])
    code = rsp['code']
    user_ref = db.reference(
        '/users/' + user_key)
    user = dict(user_ref.get())
    if ((pbkdf2_sha256.verify(code, user['token'])) == True):
        user_ref.update({
            "token": str(uuid.uuid4())
        })
        user_ref = db.reference(
            '/users/' + user_key)
        user = dict(user_ref.get())
        token = str(uuid.uuid4())
        user_ref.update({
            'token': token
        })
        main_link = get_main_link()
        link = main_link + "reset-link/" + token + "/" + user_key
        write_str = '<h4>Click <a href="' + link + \
            '">Here</a> To Reset Your Password</h4><br>'
        subject = "Password Reset for" + " Your SentinelFW Account"
        send_email([email], write_str, subject)
        print(link)
        return render_template("login/pw_reset.html")
    else:
        return render_template("msg.html", page='/login', type='danger', alert="Incorrect Auth Code")


@login_blueprint.route('/reset-link/<admin_token>/<admin_user>', methods=['GET'])
def admin_pw_reset_confirm(admin_token, admin_user):
    try:
        user_ref = db.reference('/users/' + admin_user)
        user = dict(user_ref.get())
        token = user['token']
        if(token == admin_token):
            return render_template("login/confirm_pw.html", user=admin_user)
        else:
            return(redirect(url_for('login.login')))
    except Exception as e:
        return(redirect(url_for('login.login')))


@login_blueprint.route('/pw-reset-confirm/<user>', methods=['POST'])
def reset_admin_pw(user):
    request.parameter_storage_class = ImmutableOrderedMultiDict
    rsp = dict((request.form))
    user_ref = db.reference('/users/' + user)
    hash_pw = pbkdf2_sha256.hash(str(rsp['password']))
    token = str(uuid.uuid4())
    user_ref.update({
        "pw": hash_pw,
        "token": token,
        "time": time.time()
    })
    return render_template("msg.html", page='/login', type='success', alert="Password Reset")
