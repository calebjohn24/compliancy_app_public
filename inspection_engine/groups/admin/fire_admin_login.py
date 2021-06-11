from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name
from import_modules import *
import plivo

login_blueprint = Blueprint(
    'fire_admin_login', __name__, template_folder='templates')


client = plivo.RestClient(auth_id='AUTH_ID',
                          auth_token='AUTH_TOKEN')

stripe.api_key = "STRIPE_KEY"

bot_number = "14255992978"


def admin_user_token(user, token):
    path_user = '/companies/' + comp_name + "/admin/" + users
    user_data = dict(db.reference(path_user).get())
    if((user_data["token"] == token) and (time.time() - user_data["time"] < 3600)):
        db.reference(path_user).update({"time": time.time()})
        return 0
    else:
        return 1


def check_comp(comp_name):
    try:
        path_user = '/companies/' + comp_name + "/admin"
        print(path_user)
        user = dict(db.reference(path_user).get())
        if(user == None):
            return 1
        else:
            return 0
    except Exception:
        return 1


@login_blueprint.route('/<comp_name>/admin-login')
def admin_login(comp_name):
    if (check_comp(comp_name) == 0):
        info_ref = db.reference('/companies/' + comp_name + "/info")
        info = dict(info_ref.get())
        logo = info['logo']
        return render_template("admin/login.html", comp_name=get_display_name(comp_name), logo=logo)
    else:
        return render_template("user/error-page.html", comp_name=get_display_name(comp_name), error="Invalid Company Name")


@login_blueprint.route('/<comp_name>/admin-login', methods=['POST'])
def admin_login_check(comp_name):
    request.parameter_storage_class = ImmutableOrderedMultiDict
    rsp = dict((request.form))
    email = str(rsp['email'])
    email = email.replace(".", "-")
    pw = rsp['pw']
    print(pw)
    print(email)
    try:
        path_user = '/companies/' + comp_name + "/admin"
        print(path_user)
        user = dict(db.reference(path_user).get())
        print(user)
        pass_hash = user[email]['pw']
        pass_check = pbkdf2_sha256.verify(pw, pass_hash)
        print(pass_check)
        token = str(uuid.uuid4())
        if(pass_check == True):
            db.reference('/companies/' + comp_name + "/admin/" + email).update({
                "time": time.time(),
                "token": token
            })
            session['admin-user'] = email
            session['admin-token'] = token
            return(redirect(url_for('fire_admin_panel.admin_panel', comp_name=comp_name)))
            # return "works"
        else:
            return(redirect(url_for('fire_admin_login.admin_login_redo', comp_name=comp_name)))
    except Exception as e:
        print(e)
        return(redirect(url_for('fire_admin_login.admin_login_redo', comp_name=comp_name)))


@login_blueprint.route('/<comp_name>/admin-login2')
def admin_login_redo(comp_name):
    check_comp(comp_name)
    info_ref = db.reference('/companies/' + comp_name + "/info")
    info = dict(info_ref.get())
    logo = info['logo']
    return render_template("admin/login2.html", comp_name=get_display_name(comp_name), logo=logo)


@login_blueprint.route('/<comp_name>/admin-2fa', methods=['POST'])
def send_2fa(comp_name):
    rsp = dict((request.form))
    reset_user = str(rsp['email']).replace(".", "-")
    try:
        user_ref = db.reference(
            '/companies/' + str(comp_name) + '/admin/' + reset_user)
        user = dict(user_ref.get())
        token = str(random.randint(100000, 999999))
        number = '1' + user['number']
        hash_val = pbkdf2_sha256.hash(token)
        user_ref.update({'token': hash_val})
        try:
            message_created = client.messages.create(
                src=bot_number,
                dst=number,
                text='Your Inspection Engine Auth Code Is: ' + token
            )
            return render_template("admin/2fa.html", number=number[-4:], email=reset_user)
        except Exception as e:
            print(e, 'error')
            return render_template("admin/2fa.html", number='invalid')
    except Exception as e:
        error = "This Account Does Not Exist"
        error = str(e)
        return(redirect(url_for('error', comp_name=comp_name, error=error)))


@login_blueprint.route('/<comp_name>/admin_pw_reset', methods=['POST'])
def admin_pw_reset(comp_name):
    rsp = dict((request.form))
    reset_user = rsp['email']
    email = str(reset_user)
    code = rsp['code']
    user_ref = db.reference(
        '/companies/' + str(comp_name) + '/admin/' + reset_user)
    user = dict(user_ref.get())
    if ((pbkdf2_sha256.verify(code, user['token'])) == True):
        user_ref.update({
            "token": str(uuid.uuid4())
        })
        user_ref = db.reference(
            '/companies/' + str(comp_name) + '/admin/' + reset_user)
        user = dict(user_ref.get())
        token = str(uuid.uuid4())
        user_ref.update({
            'token': token
        })
        info_ref = db.reference('/companies/' + comp_name + "/info")
        info = dict(info_ref.get())
        logo = info['logo']
        main_link = get_main_link()
        link = main_link + comp_name + "/admin-reset-link~" + token + "~" + reset_user
        write_str = '<h4>Click <a href="' + link + \
            '">Here</a> To Reset Your Password</h4><br>'
        write_str += '<img src="' + logo + '">'
        subject = "Password Reset for " + \
            str(get_display_name(comp_name)) + " Admin Account"
        send_email([email], write_str, subject)
        return render_template("admin/pw_reset.html", comp_name=get_display_name(comp_name))
    else:
        return render_template("msg.html", page='/login', type='danger', alert="Incorrect Auth Code")


@login_blueprint.route('/<comp_name>/admin-reset-link~<admin_token>~<admin_user>', methods=['GET'])
def admin_pw_reset_confirm(comp_name, admin_token, admin_user):
    try:
        user_ref = db.reference(
            '/companies/' + str(comp_name) + '/admin/' + admin_user)
        user = dict(user_ref.get())
        token = user['token']
        if(token == admin_token):
            return render_template("admin/confirm_pw.html", comp_name=get_display_name(comp_name), user=admin_user)
        else:
            return render_template("user/error-page.html", comp_name=get_display_name(comp_name), error="Account Not Found")
    except Exception as e:
        return render_template("user/error-page.html", comp_name=get_display_name(comp_name), error="Account Not Found")


@login_blueprint.route('/<comp_name>/admin-pw-reset-confirm~<user>', methods=['POST'])
def reset_admin_pw(comp_name, user):
    request.parameter_storage_class = ImmutableOrderedMultiDict
    rsp = dict((request.form))
    user_ref = db.reference('/companies/' + str(comp_name) + '/admin/' + user)
    hash = pbkdf2_sha256.hash(str(rsp['password']))
    token = str(uuid.uuid4())
    user_ref.update({
        "pw": hash,
        "token": token,
        "time": time.time()
    })
    session['admin-user'] = user
    session['admin-token'] = token
    return render_template("alert.html", alert="Password Reset", page=str("/" + comp_name + "/admin-panel"))
