from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name, check_fire_zone
from import_modules import *


storage_client = storage.Client.from_service_account_json(
    "compliancy-app-firebase-adminsdk-bd193-f9c1957881.json")
bucket = storage_client.get_bucket("compliancy-app.appspot.com")

panel_blueprint = Blueprint(
    'fire_user_panel', __name__, template_folder='templates')


def check_user_token(user_id, token):
    try:
        user_data = db.reference('/users/' + user_id).get()
        user_token = user_data['token']
        if(user_token == token):
            return 0
        else:
            return 1
    except Exception as e:
        return 1


@panel_blueprint.route('/<comp_name>/view-report/<report_id>/<report_token>/<user_type>')
def gen_report(comp_name, report_id, report_token, user_type):
    report = db.reference('/reports/' + report_id).get()
    user_type = user_type
    if (user_type == 'tech'):
        user_id = session.get('id', None)
        token = session.get('token', None)
        if(check_user_token(user_id, token) == 1):
            return(redirect(url_for('login.login')))
    elif (user_type == 'admin'):
        token = session.get('token', None)
        user_id = session.get('id', None)
        if(check_user_token(user_id, token) == 1):
            return(redirect(url_for('login.login')))
    elif (user_type == 'fire-admin'):
        token = session.get('token', None)
        user_id = session.get('id', None)
        if(check_user_token(user_id, token) == 1):
            return(redirect(url_for('login.login')))
    elif (user_type == 'public'):
        if(report_token != report['token']):
            referrer = request.headers.get("Referer")
            return (redirect(referrer), 302)

    if (report_token == report['token']):
        system = report['system']
        system = db.reference('/systems/' + system).get()
        brand = system['brand']
        cert_check = db.reference(
            '/jurisdictions/' + report['zone'] + '/info/check_cert').get()
        tech_cert = db.reference(
            '/jurisdictions/' + report['zone'] + '/info/check_tech_cert').get()
        if (cert_check == 'yes'):
            cert = db.reference('/companies/' + report['comp'] +
                                '/info/certs/' + system['brand'] + '/img').get()
        else:
            cert = '-'
        user_info = db.reference(
            '/companies/' + report['comp'] + '/users/' + report['user_id']).get()
        session['click'] = 'reports-tab'
        print(user_type)
        return(render_template('report-pdf-template.html', user_type=user_type, system=system, tech_cert=tech_cert, comp_name=get_display_name(report['comp']), comp_id=report['comp'], report_id=report_id, report=report, user_email=report['user_id'], cert_check=cert_check, cert=cert, user=user_info))
    else:
        referrer = request.headers.get("Referer")
        return (redirect(referrer), 302)


@panel_blueprint.route('/api/get-amends', methods=['POST'])
def get_amends():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):
        amends_bool = True

        try:
            amends = db.reference('/companies/' + comp_name + '/amend').get()
        except Exception as e:
            amends = {}
            amends_bool = False

        if(amends == None):
            amends = {}
            amends_bool = False

        packet = {
            'amends': amends,
            'amends_bool': amends_bool
        }

        return packet
    else:
        return {'error': 403}


@panel_blueprint.route('/api/homepage-info', methods=['POST'])
def get_homepage_info():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):
        comp_disp_name = get_display_name(comp_name)
        comp_logo = str(db.reference(
            '/companies/' + comp_name + '/info/logo').get())
        packet = {'logo': comp_logo,
                  'dispName': comp_disp_name}
        return packet
    else:
        return {'error': 403}


@panel_blueprint.route('/api/user-info', methods=['POST'])
def get_user_info():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):
        comp_info = dict(db.reference(
            '/companies/' + comp_name + '/info').get())
        user_info = dict(db.reference('/users/' + user_id).get())
        comp_logo = comp_info['logo']
        comp_disp_name = get_display_name(comp_name)
        packet = {'logo': comp_logo,
                  'dispName': comp_disp_name,
                  'compInfo': comp_info,
                  'userInfo': user_info}
        return packet
    else:
        return {'error': 403}


@panel_blueprint.route('/api/company-certs', methods=['POST'])
def get_comp_certs():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):
        packet = {}
        certs = db.reference('/companies/' + comp_name + '/info/certs').get()
        packet = {'certs': certs}
        return packet
    else:
        return {'error': 403}


@panel_blueprint.route('/api/change-user-info', methods=['POST'])
def change_user_input():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):
        print(rsp)
        change_type = str(rsp['changeType'])
        new_data = str(rsp['newData'])
        db.reference('/users/' + user_id).update(
            {change_type: new_data}
        )

        packet = {'success': True}
        return packet
    else:
        return {'error': 403}


@panel_blueprint.route('/api/list-systems', methods=['POST'])
def list_systems():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):

        cert_zones = set(
            dict(db.reference('/companies/' + comp_name + '/info/zones').get()).keys())
        no_cert_zones = set()
        all_zones = set(dict(db.reference('/jurisdictions').get()).keys())

        for az in all_zones:
            check_cert = db.reference(
                '/jurisdictions/' + az + '/info/check_cert').get()
            if (check_cert != 'yes'):
                no_cert_zones.add(az)

        zones_total = no_cert_zones.union(cert_zones)

        systems_final = {}

        system_keys = set()

        for cz in zones_total:
            systems = dict(db.reference(
                '/systems').order_by_child('zone').equal_to(cz).get())

            for h in systems:
                if (h not in system_keys):
                    system_keys.add(h)
                    systems_final.update({h: systems[h]})

        packet = {"systems": systems_final}

        return packet
    else:
        print("no auth")
        return {'error': 403}


@panel_blueprint.route('/api/system-info', methods=['POST'])
def system_info():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    print(rsp)
    if(check_user_token(user_id, token) == 0):
        system_id = str(rsp['systemId'])
        system = db.reference('/systems/' + system_id).get()
        packet = {'system': system}
        return packet
    else:
        print("no auth")
        return {'error': 403}


@panel_blueprint.route('/api/view-reports', methods=['POST'])
def view_reports():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):
        system_id = rsp['systemId']
        report_ref = db.reference("/reports")
        try:
            reports = dict(report_ref.order_by_child(
                'system').equal_to(system_id).get())
        except Exception:
            reports = {}
        finally:
            packet = {'reports': reports}
            return packet
    else:
        print("no auth")
        return {'error': 403}
