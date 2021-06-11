from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name
from import_modules import *
import plivo

client = plivo.RestClient(auth_id='AUTH_ID',
                          auth_token='AUTH_TOKEN')
bot_number = "14255992978"

login_blueprint = Blueprint(
    'fire_user_login', __name__, template_folder='templates')


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

@login_blueprint.route('/api/new_user_token', methods=['POST'])
def user_login():
    rsp = dict(request.json)
    email = str(rsp['email']).lower()
    email = str(email).replace(' ','')
    pw = str(rsp['pw'])
    db_email = dict(db.reference(
        '/users').order_by_child('email').equal_to(email).get())
    if (db_email == {}):
        packet = {'auth':False,
        'token':'NA',
        'userId':'NA',
        'compId':'NA'}
        return packet
    else:
        for key in db_email:
            pw_hash = db_email[key]['pw']
            comp = db_email[key]['comp']
            pass_check = pbkdf2_sha256.verify(pw, pw_hash)
            if (pass_check == True):
                acct_type = db_email[key]['type']
                token = str(uuid.uuid4())
                if (acct_type == 'tech'):
                    db.reference('/users/' + key).update({
                        "time": time.time(),
                        "token": token
                    })
                    packet = {'auth':True,
                                'token':token,
                                'userId':key,
                                'compId':comp}
                    return packet
                else:
                    packet = {'auth':False,
                        'token':'NA',
                        'userId':'NA',
                        'compId':'NA'}
                    return packet
            else:
                packet = {'auth':False,
                    'token':'NA',
                    'userId':'NA',
                    'compId':'NA'}
                return packet


@login_blueprint.route('/api/check_user_token', methods=['POST'])
def check_user_login():
    rsp = dict(request.json)
    user_id = str(rsp['id']).lower()
    user_token = str(rsp['token'])
    db_email = dict(db.reference(
        '/users/' + user_id).get())
    if (db_email == {}):
        packet = {'auth':False,
        'token':'NA',
        'userId':'NA',
        'compId':'NA'}
        return packet
    else:
        pw_token = db_email['token']
        comp = db_email['comp']
        if (user_token == pw_token):
            acct_type = db_email['type']
            token = str(uuid.uuid4())
            if (acct_type == 'tech'):
                db.reference('/users/' + user_id).update({
                    "time": time.time(),
                    "token": token
                })
                packet = {'auth':True,
                            'token':token,
                            'userId':user_id,
                            'compId':comp}
                return packet
            else:
                packet = {'auth':False,
                    'token':'NA',
                    'userId':'NA',
                    'compId':'NA'}
                return packet
        else:
            packet = {'auth':False,
                'token':'NA',
                'userId':'NA',
                'compId':'NA'}
            return packet

