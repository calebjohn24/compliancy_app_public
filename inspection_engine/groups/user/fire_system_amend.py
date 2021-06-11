from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name
from import_modules import *


storage_client = storage.Client.from_service_account_json(
    "compliancy-app-firebase-adminsdk-bd193-f9c1957881.json")
bucket = storage_client.get_bucket("compliancy-app.appspot.com")


system_amend_blueprint = Blueprint(
    'system_amend_blueprint', __name__, template_folder='templates')


stripe.api_key = 'STRIPE_KEY'


def check_user_token(user, token):
    try:
        path_user = "/users/" + user
        user_data = dict(db.reference(path_user).get())
        if((user_data["token"] == token) and (time.time() - user_data["time"] < 3600)):
            db.reference(path_user).update({"time": time.time()})
            return 0
        else:
            return 1
    except Exception:
        return 1


@system_amend_blueprint.route('/<comp_name>/system-report-amend', methods=['POST'])
def pick_report(comp_name):
    rsp = dict(request.form)
    code = rsp['code']
    amend = dict(db.reference('/companies/' +
                              comp_name + '/amend/' + code).get())
    system_id = amend['system']
    reason = amend['reason']
    report_id = amend['report']
    report = dict(db.reference('/reports/' + report_id).get())
    db.reference('/reports/' + report_id).update({
        'amend': 'yes'
    })
    form_id = report['form_id']
    session['inspect-code'] = report_id
    session['test-code'] = system_id
    session['form'] = form_id
    system_ref = db.reference('/systems/' + system_id)
    system_info = dict(system_ref.get())
    user = session.get('user', None)
    name = session.get('name', None)
    rest_name = system_info['name']
    addr = system_info['addr']
    city = system_info['city']
    state = system_info['state']
    zip = system_info['zip']
    phone = system_info['phone']
    model = system_info['model']
    owner = system_info['owner']
    email = system_info['email']
    location = system_info['location']
    address = addr + " " + city + " " + state + " " + zip
    session['zone'] = system_info['zone']
    now = datetime.datetime.now()
    rem_ref = db.reference('/companies/' +
                           comp_name + '/amend/' + code)
    rem_ref.delete()
    return render_template("user/testing/check_info.html", comp_name=get_display_name(comp_name), email=email, code=system_id, address=address, rest_name=rest_name, phone=phone, model=model, owner=owner, location=location, reason=reason)
