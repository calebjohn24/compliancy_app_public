from uuid import uuid4
from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name, resize_photo, upload_file
from import_modules import *


storage_client = storage.Client.from_service_account_json(
    "compliancy-app-firebase-adminsdk-bd193-f9c1957881.json")
bucket = storage_client.get_bucket("compliancy-app.appspot.com")


system_test_blueprint = Blueprint(
    'system_test_blueprint', __name__, template_folder='templates')


stripe.api_key = 'STRIPE_KEY'


def check_user_token(user_id, token):
    try:
        user_data = db.reference('/users/' + user_id).get()
        user_token = user_data['token']
        if(user_token == token):
            return 0
        else:
            return 1
    except Exception as e:
        print(e)
        return 1


def check_fire_zone(comp_name, zone):
    try:
        comp_info_ref = db.reference('/companies/' + comp_name + "/info/zones")
    # print(comp_info_ref.get())
        comp_zones = list(dict(comp_info_ref.get()).keys())
        set_comp_zones = set(comp_zones)
        if(zone in set_comp_zones):
            return 0
        else:
            return 1
    except Exception:
        return 1


def bill_client(comp_name):
    try:
        info_ref = db.reference('/companies/' + comp_name + '/billing')
        info = dict(info_ref.get())

        if(info['trial'] == 'no'):
            stripe.Charge.create(
                amount=int((info['price'] * 1.1) * 100), 
                currency='usd',
                customer=info['stripe_id']
            )

        count = info['count']
        count += 1
        info_ref.update({
            'count': count
        })

        return True
    except stripe.error.CardError as e:
        print(e.user_message)
        write_str = "<h4>Your Payment Method Was Declined With The Following Message: \n</h4><br>"
        write_str += "<h3>"+ e.user_message +" \n</h3><br>"
        write_str += "<h4>Your company will not be able to file reports till your billing issue is resolved. \n"
        write_str += "Please update your billing method in the billing panel on your admin dashboard, or contact us to resolve this issue.</h4><br>"
        subject = 'Billing Issue With Your Sentinel Account'
        comp_accts = dict(db.reference('/users').order_by_child('comp').equal_to(comp_name).get())
        comp_emails_keys = list(comp_accts.keys())
        comp_emails = []
        for c in comp_emails_keys:
            if(comp_accts[c]['type'] == 'admin'):
                comp_emails.append(str(comp_accts[c]['email']))
        send_email(comp_emails, write_str, subject)
        return False


def log_report(comp_name, user_id, report_id):
    report = dict(db.reference('/reports/' + report_id).get())

    log_key = (db.reference('/companies/' +
                            comp_name + '/billing/log_key').get())
    user_log_ref = db.reference(
        '/companies/' + comp_name + '/log/' + log_key + '/users/' + user_id)
    comp_log_ref = db.reference('/companies/' + comp_name + '/log/' + log_key)
    curr_user_log = dict(user_log_ref.get())
    comp_log = dict(comp_log_ref.get())
    tag = report['tag']

    tag_count_user = curr_user_log['tags'][str(tag).lower()]
    tag_count_comp = comp_log['tags'][str(tag).lower()]

    tag_count_user += 1
    tag_count_comp += 1

    db.reference('/companies/' + comp_name + '/log/' +
                 log_key + '/users/' + user_id + '/tags/').update({
                     str(tag).lower(): tag_count_user
                 })

    db.reference('/companies/' + comp_name + '/log/' +
                 log_key + '/tags/').update({
                     str(tag).lower(): tag_count_comp
                 })

    report_comp_count = comp_log['reports']
    report_user_count = curr_user_log['reports']

    report_comp_count += 1
    report_user_count += 1

    db.reference('/companies/' + comp_name + '/log/' +
                 log_key + '/users/' + user_id).update({
                     'reports': report_user_count
                 })

    db.reference('/companies/' + comp_name + '/log/' +
                 log_key).update({
                     'reports': report_comp_count
                 })

    return


def check_cert(comp_name, zone, system):
    zone_cert = db.reference(
        '/jurisdictions/' + zone + '/info/check_cert').get()
    if(zone_cert == 'yes'):
        system_info = dict(db.reference('/systems/' + system).get())
        comp_certs = set(
            dict(db.reference('/companies/' + comp_name + '/info/certs').get()).keys())
        system_cert = system_info['brand']
        if (system_cert in comp_certs):
            return 0
        else:
            return 1
    else:
        return 0


@system_test_blueprint.route('/api/system_inspect/list_forms', methods=['POST'])
def list_forms():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):
        system_id = str(rsp['systemId'])
        system = db.reference('/systems/' + system_id).get()

        zone = system['zone']
        system_type = system['type']

        forms_ref = db.reference('/jurisdictions/' + zone + '/form')
        try:
            forms = dict(forms_ref.order_by_child(
                'system_type').equal_to(system_type).get())
            reportId = str(uuid.uuid4())[:8]
        except Exception as e:
            print(e)
            forms = {}
            reportId = ''

        packet = {'forms': forms, 'zone': zone, 'reportId': reportId}
        return packet
    else:
        return {'error': 403}


@system_test_blueprint.route('/api/system_inspect/inspect', methods=['POST'])
def get_questions():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):
        system_id = str(rsp['systemId'])
        zone = str(rsp['zoneId'])
        form_id = str(rsp['formId'])
        form_index = int(rsp['formIndex'])
        report_id = str(rsp['reportId'])
        question_list = list(db.reference(
            '/jurisdictions/' + zone + '/form/' + form_id + '/questions').get())
        if(form_index < len(question_list)):
            question_id = question_list[form_index]
            question_data = db.reference(
                '/jurisdictions/' + zone + '/questions/' + question_id).get()
            form_complete = False
        else:
            form_complete = True
            question_data = {}
            print('form done')

        if(form_index == 0):
            tag = 'White'
        else:
            tag = str(db.reference('/tmp/reports/' + report_id + '/tag').get())

        packet = {
            'question': question_data,
            'formComplete': form_complete,
            'tag': tag
        }
        return packet
    else:
        return {'error': 403}


@system_test_blueprint.route('/api/system_inspect/delete_report', methods=['POST'])
def delete_report():
    rsp = dict(request.json)
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):
        report_id = rsp['reportId']
        report_ref = db.reference('/tmp/reports/' + report_id)
        try:
            report_ref.delete()
        except Exception as e:
            print(e)
            pass
        finally:
            return {'success': True}
    else:
        return {'error': 403}


@system_test_blueprint.route('/api/system_inspect/start_amend', methods=['POST'])
def clear_amend():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):
        success = True
        amend_code = rsp['amendCode']

        rem_ref = db.reference('/companies/' + comp_name + '/amend/' + amend_code)
        rem_ref.delete()


        packet = {'success': success}
        return packet
    else:
        return {'error': 403}

@system_test_blueprint.route('/api/system_inspect/submit_question', methods=['POST'])
def sub_question_data():
    rsp = dict(request.form)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):
        success = True
        # try:
        system_id = rsp['systemId']
        zone_id = rsp['zoneId']
        form_id = rsp['formId']
        form_index = int(rsp['formIndex'])
        report_id = rsp['reportId']
        print(form_index)

        user_info = dict(db.reference('/users/' + user_id).get())
        system_info = dict(db.reference('/systems/' + system_id).get())
        report_tmp_ref = db.reference('/tmp/reports/' + report_id)

        current_questions = []
        current_tag = 'White'
        if(form_index == 0):
            amend_bool = False

            try:
                old_report = db.reference('/reports/' + report_id).get()
                if(old_report['amend'] == 'yes'):
                    amend_bool = True
            except Exception:
                amend_bool = False

            if(amend_bool):
                report_init = {
                    'amend': 'yes',
                    'user_id': user_id,
                    'author': user_info['name'],
                    'email': system_info['email'],
                    'comp': comp_name,
                    'system': system_id,
                    'cert': 'UNCERTIFIED',
                    'tag': 'White'
                }

            else:
                report_token = str(uuid.uuid4())
                report_init = {
                    'time_stamp': str(str(datetime.datetime.now())[:-10]),
                    'complete': 1,
                    'user_id': user_id,
                    'author': user_info['name'],
                    'email': system_info['email'],
                    'form_id': form_id,
                    'amend': 'no',
                    'comp': comp_name,
                    'system': system_id,
                    'time': time.time(),
                    'zone': zone_id,
                    'token': report_token,
                    'cert': 'UNCERTIFIED',
                    'tag': 'White'
                }
            report_tmp_ref.update(report_init)

        current_report = report_tmp_ref.get()

        if(form_index > 0):
            current_questions = list(current_report['form'])
            current_tag = current_report['tag']

        response_data = {'question': rsp['question']}

        if('photoLabel' in rsp):
            file = request.files['photo']
            old_filename = secure_filename(file.filename)
            filename = ('tmp/' + str(old_filename) + '-' +
                        report_id + '-' + str(form_index) + '-photo.jpg')
            mimetype = 'image/jpeg'
            file.save(filename)
            optimized_file = resize_photo(filename)
            url = upload_file(optimized_file, mimetype)
            photo_data = {
                'data': url,
                'descrip': rsp['photoLabel']
            }

            response_data.update({'photo': photo_data})

        if('check' in rsp):
            response_data.update({'check': rsp['check']})

            check_tag = rsp['checkTag']

            if(current_tag == 'White'):
                if(check_tag == 'yellow' or check_tag == 'red'):
                    current_tag = str(check_tag).capitalize()
            elif(current_tag == 'yellow'):
                if(check_tag == 'red'):
                    current_tag = str(check_tag).capitalize()

        if('mul' in rsp):
            response_data.update({'mul': rsp['mul']})

            mul_tag = rsp['mulTag']
            if(current_tag == 'White'):
                if(mul_tag == 'yellow' or mul_tag == 'red'):
                    current_tag = str(mul_tag).capitalize()
            elif(current_tag == 'yellow'):
                if(mul_tag == 'red'):
                    current_tag = str(mul_tag).capitalize()

        if('text' in rsp):
            response_data.update({'text': {
                'data': rsp['text'],
                'label': rsp['textLabel']
            }})

        current_questions.append(response_data)
        report_tmp_ref.update({
            'tag': current_tag,
            'form': current_questions
        })

        '''
        except Exception as e:
            print(e)
            print('error')
            raise e
            success = False
        finally:
        '''
        packet = {'success': success}
        return packet
    else:
        return {'error': 403}


@system_test_blueprint.route('/api/system_inspect/submit_report', methods=['POST'])
def submit_report():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):
        success = True
        system_id = rsp['systemId']
        zone_id = rsp['zoneId']
        report_id = rsp['reportId']

        report_tmp_ref = db.reference('/tmp/reports/' + report_id)

        current_report = dict(report_tmp_ref.get())

        report_ref = db.reference('/reports')

        if(current_report['amend'] == 'yes'):
            report_ref = db.reference('/reports/' + report_id)
            report_ref.update(current_report)
        else:
            if(bill_client(comp_name)):
                report_ref = db.reference('/reports/')
                current_report.update({
                    'duration': (time.time() - float(current_report['time'])),
                    'form_name': rsp['formName']
                })
                report_ref.update({report_id: current_report})
                db.reference('/systems/' + system_id).update({
                    'last_inspect': str(str(datetime.datetime.now())[:-10]),
                    'last_inspect_epoch': time.time()
                })
            else:
                success = False
                return {'success': success}

        log_report(comp_name, user_id, report_id)

        req_ref = db.reference('/jurisdictions/' +
                               zone_id + '/requests/reports')
        req_ref.push({
            'report_id': report_id,
            'comp': comp_name,
            'system': system_id
        })

        return {'success': success}
    else:
        return {'error': 403}
