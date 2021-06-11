from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name, check_fire_zone, resize_photo, upload_file
from import_modules import *
import threading
import queue

storage_client = storage.Client.from_service_account_json(
    "compliancy-app-firebase-adminsdk-bd193-f9c1957881.json")
bucket = storage_client.get_bucket("compliancy-app.appspot.com")

panel_blueprint = Blueprint(
    'fire_gov_panel', __name__, template_folder='templates')


def check_user_token(user_id, token):
    path_user = '/users/' + user_id
    user_data = dict(db.reference(path_user).get())
    if ((user_data["token"] == token) and (time.time() - user_data["time"] < 3600)):
        db.reference(path_user).update({"time": time.time()})
        return 0
    else:
        return 1


@panel_blueprint.route('/fire-admin/<zone>/panel')
def panel(zone):
    st = time.time()
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))

    logo = str(db.reference('/jurisdictions/' + zone + '/info/logo').get())



    try:
        request_data = db.reference(
            '/jurisdictions/' + zone + '/requests').get()
    except Exception as e:
        request_data = {}

    if(request_data == None):
        request_data = {}

    return render_template('gov/panel_new.html', id=zone, logo=logo, request_data=request_data)


@panel_blueprint.route('/fire-admin/<zone>/systems')
def view_systems(zone):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)

    info = db.reference('/jurisdictions/' + zone + '/info').get()

    longitude = info['long']
    lattitude = info['lat']

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))

    info = dict(db.reference('/jurisdictions/' + zone).get())
    try:
        # print(info)
        systems = dict(db.reference(
            '/systems').order_by_child('zone').equal_to(zone).get())
    except Exception as e:
        print(e, "error-systems")
        systems = {}

    return render_template('gov/systems.html', id=zone, systems=systems, longitude=longitude, lattitude=lattitude)


@panel_blueprint.route('/fire-admin/<zone>/reports')
def view_reports(zone):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))

    info = dict(db.reference('/jurisdictions/' + zone).get())

    try:
        reports_ref = db.reference('/reports')
        reports = reports_ref.order_by_child('zone').equal_to(zone).get()
        if (reports == None):
            reports = {}
    except Exception as e:
        print(e, "error-reports")
        reports = {}

    return render_template('gov/reports.html', id=zone, reports=reports)


@panel_blueprint.route('/fire-admin/<zone>/companies')
def view_comps(zone):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))

    try:
        comp_ref = db.reference('/jurisdictions/' + zone + '/companies')
        companies = {}
        if (comp_ref.get() != None):
            for k_c, v_c in dict(comp_ref.get()).items():
                info_dict = dict(db.reference(
                    '/companies/' + str(k_c) + '/info').get())
                companies.update({
                    k_c: info_dict
                })
        else:
            companies = {}
    except Exception as e:
        print(e, "error-comps")
        companies = {}

    info = db.reference('/jurisdictions/' + zone + '/info').get()

    longitude = info['long']
    lattitude = info['lat']

    return render_template('gov/companies.html', id=zone, companies=companies, longitude=longitude, lattitude=lattitude)


@panel_blueprint.route('/fire-admin/<zone>/rules')
def view_rules(zone):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))

    info = db.reference('/jurisdictions/' + zone + '/info').get()
    return render_template('gov/rules.html', id=zone, info=info)


@panel_blueprint.route('/fire-admin/<zone>/check-report/<request_id>')
def check_report(zone, request_id):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))

    req = dict(db.reference('/jurisdictions/' + zone +
                            '/requests/reports/' + request_id).get())

    report_id = req['report_id']
    system_id = req['system']

    print(report_id)

    system = db.reference('/systems/' + system_id).get()

    report = dict(db.reference('/reports/' + report_id).get())

    cert_check = db.reference(
        '/jurisdictions/' + report['zone'] + '/info/check_cert').get()
    tech_cert = db.reference(
        '/jurisdictions/' + report['zone'] + '/info/check_tech_cert').get()
    if (cert_check == 'yes'):
        cert = db.reference('/companies/' + report['comp'] +
                            '/info/certs/' + system['brand'] + '/img').get()
    else:
        cert = '-'

    user_info = db.reference('/users/' + report['user_id']).get()

    return (render_template('gov/approve-report-new.html', system=system, tech_cert=tech_cert, zone=zone, request_id=request_id,
                            comp_name=get_display_name(report['comp']), comp_id=report['comp'], report_id=report_id,
                            report=report, cert_check=cert_check, cert=cert,
                            user=user_info, id=zone))


@panel_blueprint.route('/fire-admin/<zone>/change-form-tag', methods=['POST'])
def change_system_report_tag(zone):
    rsp = dict(request.form)

    request_id = rsp['request_id']

    new_tag = rsp['tag']

    system_id = rsp['system_id']
    report_id = rsp['report_id']
    report_data = db.reference('/reports/' + report_id).get()
    comp_name = report_data['comp']
    user_id = report_data['user_id']

    log_key = (db.reference('/companies/' +
                            comp_name + '/billing/log_key').get())
    user_log_ref = db.reference(
        '/companies/' + comp_name + '/log/' + log_key + '/users/' + user_id)
    comp_log_ref = db.reference('/companies/' + comp_name + '/log/' + log_key)
    curr_user_log = dict(user_log_ref.get())
    comp_log = dict(comp_log_ref.get())
    tag = report_data['tag']

    tag_count_user = curr_user_log['tags'][str(tag).lower()]
    tag_count_comp = comp_log['tags'][str(tag).lower()]

    tag_count_user -= 1
    tag_count_comp -= 1

    db.reference('/companies/' + comp_name + '/log/' +
                 log_key + '/users/' + user_id + '/tags/').update({
                     str(tag).lower(): tag_count_user
                 })

    db.reference('/companies/' + comp_name + '/log/' +
                 log_key + '/tags/').update({
                     str(tag).lower(): tag_count_comp
                 })
    

    new_tag_count_user = curr_user_log['tags'][str(new_tag).lower()]
    new_tag_count_comp = comp_log['tags'][str(new_tag).lower()]

    new_tag_count_user += 1
    new_tag_count_comp += 1

    db.reference('/companies/' + comp_name + '/log/' +
                 log_key + '/users/' + user_id + '/tags/').update({
                     str(new_tag).lower(): new_tag_count_user
                 })

    db.reference('/companies/' + comp_name + '/log/' +
                 log_key + '/tags/').update({
                     str(new_tag).lower(): new_tag_count_comp
                 })


    report_ref = db.reference('/reports/' + report_id)
    report_ref.update({
        'tag': new_tag
    })

    system_ref = db.reference('/systems/' + system_id)
    system_ref.update({
        'tag': new_tag
    })


    return redirect(url_for('fire_gov_panel.check_report', zone=zone, request_id=request_id))


@panel_blueprint.route('/fire-admin/<zone>/change-system-tag', methods=['POST'])
def change_system_tag(zone):
    rsp = dict(request.form)

    tag = rsp['tag']

    system_id = rsp['system_id']
    print(system_id)

    system_ref = db.reference('/systems/' + system_id)
    system_ref.update({
        'tag': tag
    })

    return redirect(url_for('fire_gov_panel.view_systems', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/confirm-report', methods=['POST'])
def confirm_report(zone):
    rsp = dict(request.form)
    request_id = rsp['request_id']
    accept = rsp['accept']
    system_id = rsp['system']
    report_id = rsp['report_id']
    zone = rsp['zone']
    name = session.get('name', None)
    email = session.get('email', None)
    system_ref = db.reference('/systems/' + system_id)
    system = dict(system_ref.get())
    log_ref = db.reference('/reports/' + report_id)
    report = log_ref.get()
    if (accept == 'yes'):
        public_code = str(random.randint(100000, 999999))

        url = get_main_link() + public_code + '/view-report/' + \
            report_id + '/' + report['token'] + '/public'

        log_ref.update({
            "complete": 0,
            'cert': "Certified By: " + zone,
            'public_code': public_code,
            'url': url
        })

        system_ref.update({
            'tag': report['tag']
        })

        write_str = "<h4>" + zone + " Has Certified Your " + report['form_name']
        write_str += ' Filed @ ' + \
                     report['time_stamp'] + ' ' + \
            'For System #' + system_id + "</h4><br> Your System Has Received a " + \
            str(report['tag']).capitalize() + " Tag. \n"
        write_str += '<h5>Click <a href="' + url + \
                     '"></a> To View Your Certified Report</h5><br>' + '\n \n'

        write_str += '<h6>Please Contact ' + name + '(<a href="mailto:' + email + '">' + email + '</a>) Who Certified' + \
            ' This Report If You Have Any Questions</h6><br>' + '\n'
        subject = zone + ' Has Certified Your ' + report['form_name']
        emails = []
        emails.append(report['email'])
        emails.append(system['email'])
        send_email(emails, write_str, subject)

    elif (accept == 'no'):
        reason = rsp['reason']
        amend_code = str(random.randint(999, 10000))
        amend_ref = db.reference('/companies/' + report['comp'] + '/amend')

        system = dict(db.reference('/systems/' + system_id).get())
        report = dict(db.reference('/reports/' + report_id).get())

        log_ref.update({
            'amend': 'yes'
        })

        amend_ref.update({
            amend_code:
                {
                    'system': system_id,
                    'report': report_id,
                    'reason': reason,
                    'time_stamp': report['time_stamp'],
                    'form_id': report['form_id'],
                    'form_name':report['form_name'],
                    'zone': zone
                }
        })

        write_str = "<h4>" + zone + \
                    " requested amendments to the " + report['form_name']
        write_str += ' Filed @ ' + \
                     report['time_stamp'] + ' ' + \
                     'For System #' + system_id + '</h4><br><br>'
        write_str += '<h5>The following changes have been requested:</h5><br>' + '\n' + '\n'
        write_str += '<h6>"' + reason + '"</h6><br>' + '\n'
        write_str += '<h5>Use Amend Code: ' + amend_code + ' to make these changes</h5>' + '\n' + '\n'

        write_str += '<h6>Please Contact ' + name + '(<a href="mailto:' + email + '">' + email + '</a>) Who Requested' + \
            ' These Amendments If You Have Any Other Questions</h6><br>' + '\n'

        subject = zone + ' Has Requested Amendments To Your ' + \
            report['form_name']
        
        emails = []
        emails.append(report['email'])
        send_email(emails, write_str, subject)

        write_str = "<h4>" + zone + \
                    " requested amendments to the " + report['form_name']
        write_str += ' Filed @ ' + \
                     report['time_stamp'] + ' ' + \
            'For System #' + system_id + '</h4><br>'
        write_str += '<h5>The following changes have been requested:</h5><br>'
        write_str += '<h6>"' + reason + '"</h6><br>'
        write_str += "<h5>We have contacted the technician that conducted the inspection to make these amendments</h5><br>" + '\n' + '\n'
        write_str += '<h6>Please Contact ' + name + '(<a href="mailto:' + email + '">' + email + '</a>) Who Requested' + \
            ' These Amendments Or '+ get_display_name(report['comp']) +', The Company That Performed This Inspection If You Have Any Other Questions</h6><br>' + '\n'
        subject = zone + ' Has Requested Amendments To Your ' + \
            report['form_name']
        emails = []
        emails.append(system['email'])
        send_email(emails, write_str, subject)

    rem_ref = db.reference('/jurisdictions/' + zone +
                           '/requests/reports/' + request_id)
    rem_ref.delete()
    return redirect(url_for('fire_gov_panel.panel', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/deauth-comp', methods=['POST'])
def deauth_comp(zone):
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)
    rsp = dict(request.form)
    rem_comp = rsp['comp']
    rem_ref = db.reference('/jurisdictions/' + zone + '/companies/' + rem_comp)
    comp_data = rem_ref.get()
    emails = list(dict(comp_data['admin']).keys())
    write_str = "<h4>" + zone + \
                " Revoked your ability to do inspections in their jurisdiction</h4><br>"
    write_str += "<h5>You can email " + \
                 str(email) + \
                 " to learn more about why your certification was revoked</h5><br>"
    subject = zone + ' Has Revoked Your Certification'
    send_email([emails], write_str, subject)
    rem_ref.delete()
    session['click'] = 'companies-tab'
    return redirect(url_for('fire_gov_panel.panel', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/change-phone', methods=['POST'])
def change_phone(zone):
    rsp = dict(request.form)
    print(rsp)
    phone = rsp['phone']
    phone_ref = db.reference('/jurisdictions/' + zone + '/info')
    phone_ref.update({
        'phone': phone
    })
    session['click'] = 'info-tab'
    return redirect(url_for('fire_gov_panel.panel', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/rem-acct', methods=['POST'])
def rem_acct(zone):
    rsp = dict(request.form)
    print(rsp)
    acct = rsp['acct']
    rem_ref = db.reference('/jurisdictions/' + zone + '/accounts/' + acct)
    rem_ref.delete()
    session['click'] = 'info-tab'
    return redirect(url_for('fire_gov_panel.panel', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/add-acct', methods=['POST'])
def add_acct(zone):
    user_id = session.get('id', None)
    user_email = session.get('email', None)
    rsp = dict(request.form)
    email = rsp['email']
    if (str(email) != user_email):
        token = str(uuid.uuid4())
        acct_ref = db.reference('/users')
        new_acct = acct_ref.push({
            'token': token,
            'time': 0,
            'pw': 'pending',
            'email': email,
            'name': 'pending',
            'zone': zone,
            'type': 'fire-admin'
        })

        acct_key = new_acct.key

        write_str = "<h4>" + zone + \
                    " has send you an invite to create fire safety administrator account</h4><br>"
        link = get_main_link() + 'fire-admin/' + zone + '/acct-register/' + \
            acct_key + '/' + token
        write_str += '<h5>Click <a href="' + link + \
                     '">Here</a> to continue your sign up</h5>'
        subject = "Create Your Fire Safety Admin Account in " + zone
        send_email([email], write_str, subject)

    return redirect(url_for('fire_gov_panel.zone_profile', zone=zone))



@panel_blueprint.route('/fire-admin/<zone>/change-cert', methods=['POST'])
def change_cert(zone):
    email = session.get('email', None)
    rsp = dict(request.form)
    cert = rsp['cert']
    cert_type = rsp['type']
    if (cert_type == 'comp'):
        print(cert)
        db.reference('/jurisdictions/' + zone + '/info').update({
            'check_cert': cert
        })
        cert_exp = {
            "yes": "now requires",
            "no": "no longer requires"
        }
        try:
            companies = list(
                dict(db.reference('/jurisdictions/' + zone + '/companies').get()).keys())
            for c in companies:
                emails = []
                user_ref = db.reference('/users')
                admins = dict(user_ref.order_by_child(
                    'comp').equal_to(c).get())
                for a in admins:
                    emails.append(admins[a]['email'])
                write_str = "<h4>" + zone + \
                            " has changed their fire safety policy, and <b>" + cert_exp[cert] + "</b> that companies be " \
                    "registered to " \
                    "perform inspections in " \
                    "their " \
                    "jurisdiction</h4><br> "
                write_str += "<h4>If you have any additional questions you can contact " + \
                    '<a href="mailto:' + email + '"><b>' + email + "</b></a></h4>"

                subject = 'Changes To ' + zone + ' Fire Safety Policy'

                send_email(emails, write_str, subject)
        except Exception as e:
            print(e)

    elif (cert_type == 'tech'):
        print(cert)
        db.reference('/jurisdictions/' + zone + '/info').update({
            'check_tech_cert': cert
        })
        cert_exp = {
            "yes": "now requires",
            "no": "no longer requires"
        }
        try:
            companies = list(
                dict(db.reference('/jurisdictions/' + zone + '/companies').get()).keys())
            for c in companies:
                emails = []
                user_ref = db.reference('/users')
                admins = dict(user_ref.order_by_child(
                    'comp').equal_to(c).get())
                for a in admins:
                    emails.append(admins[a]['email'])

                write_str = "<h4>" + zone + \
                            " has changed their fire safety policy, and <b>" + cert_exp[
                                cert] + "</b> that technicians have brand " \
                                        "certifications to perform inspections in their jurisdiction</h4><br> "

                write_str += "<h4>If you have any additional questions you can contact " + \
                    '<a href="mailto:' + email + '"><b>' + email + "</b></a></h4>"

                subject = 'Changes To ' + zone + ' Fire Safety Policy'

                send_email(emails, write_str, subject)
        except Exception as e:
            print(e)
    return redirect(url_for('fire_gov_panel.view_rules', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/change-tag-override', methods=['POST'])
def change_override(zone):
    email = session.get('email', None)
    rsp = dict(request.form)
    override = rsp['override']
    override_exp = {
        "yes": "now allows",
        "no": "now does not"
    }
    try:
        companies = list(
            dict(db.reference('/jurisdictions/' + zone + '/companies').get()).keys())
        for c in companies:
            emails = []
            user_ref = db.reference('/users')
            admins = dict(user_ref.order_by_child('comp').equal_to(c).get())
            for a in admins:

                emails.append(admins[a]['email'])

            write_str = "<h4>" + zone + \
                        " has changed their fire safety policy, and <b>" + override_exp[
                            override] + '</b> technicians to override SentinelFW auto-tagging ' \
                                        'certifications to perform inspections in their jurisdiction</h4><br> '

            write_str += "<h4>If you have any additional questions you can contact " + \
                '<a href="mailto:' + email + '"><b>' + email + "</b></a></h4>"

            subject = 'Changes To ' + zone + ' Fire Safety Policy'

            send_email(emails, write_str, subject)
    except Exception as e:
        print(e)

    return redirect(url_for('fire_gov_panel.view_rules', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/change-time', methods=['POST'])
def change_time(zone):
    rsp = dict(request.form)
    days = int(rsp['days'])
    day_secs = 86400 * days
    db.reference('/jurisdictions/' + zone + '/info/filing').update({
        'days': days,
        'time': float(day_secs)
    })

    systems_ref = db.reference('/systems')
    systems = dict(systems_ref.order_by_child('zone').equal_to(zone).get())

    if (systems != {}):
        for sys_key, sys_data in systems.items():
            if(systems[sys_key]['active'] == 'yes'):
                time_diff_secs = time.time() - \
                    systems[sys_key]['last_inspect_epoch']
                time_diff_days = int(time_diff_secs / 86400)

                write_str = "<h4>" + zone + \
                            " Has changed their fire safety policy, and now requires that systems be inspected every " + str(
                                days) + ' days.<br>'
                if (time_diff_days > 1):
                    write_str += "<h4> Your system id #" + sys_key + " was last inspected on " + systems[sys_key][
                        'last_inspect'] + " and will need to reinspected in the next <b>" + str(
                        time_diff_days) + " days.</b></h4>"
                else:
                    write_str += "<h4> Your system id #" + sys_key + " was last inspected on " + systems[sys_key][
                        'last_inspect'] + " and will need to reinspected <b>as soon as possible.</b></h4>"

                subject = 'Changes To ' + zone + 'Fire Safety Policy'

                email = systems[sys_key]['email']
                send_email([email], write_str, subject)
    return redirect(url_for('fire_gov_panel.view_rules', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/system-register/<request_id>')
def register_system(zone, request_id):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)
    click = session.get('click', None)

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))

    try:
        request_ref = db.reference(
            '/jurisdictions/' + zone + '/requests/systems/' + request_id)
        request_data = request_ref.get()

        system_id = request_data['system']
        system = db.reference('/systems/' + system_id).get()

        cert = db.reference('/jurisdictions/' +
                            zone + '/info/check_cert').get()
        if (cert == 'yes'):
            reg_comp = system['reg_comp']
            cert_brand = system['brand']
            cert_img = db.reference(
                '/companies/' + reg_comp + '/info/certs/' + str(cert_brand) + '/img').get()
        else:
            cert_brand = ''
            cert_img = ''
        comp_name = get_display_name(system['reg_comp'])
        return (render_template('gov/add-system-new.html', zone=zone, request_id=request_id, system=system, comp_name=comp_name, id=zone, system_id=system_id,
                                cert=cert, cert_img=cert_img, cert_brand=cert_brand))

    except Exception as e:
        print(e, 'error')
        return (
            render_template('msg.html', page="/fire-admin/" + zone + "/panel", alert="Request Has already been handled",
                            type="success"))



@panel_blueprint.route('/fire-admin/<zone>/dismiss-past-due/<request_id>')
def dismiss_past_due(zone, request_id):
    token = session.get('token', None)
    user_id = session.get('id', None)

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))

    rem_ref = db.reference('/jurisdictions/' + zone + '/requests/past_due/' + str(request_id))
    rem_ref.delete()
    return redirect(url_for('fire_gov_panel.panel', zone=zone))

@panel_blueprint.route('/fire-admin/<zone>/confirm-system', methods=['POST'])
def register_system_2(zone):
    rsp = dict(request.form)
    confirm = rsp['confirm']
    system = rsp['system']
    request_id = rsp['request_id']
    print(confirm)
    if (confirm == 'yes'):
        system_ref = db.reference('/systems/' + system)
        system_ref.update({
            'zone': zone
        })
        system_token = str(uuid.uuid4())
        system_ref.update({
            'token': system_token
        })
        now = datetime.datetime.now()
        zone_ref = db.reference('/jurisdictions/' + zone + '/systems')
        zone_ref.update({
            system: str(now)
        })
        system_ref = db.reference('/systems/' + system)
        system_data = system_ref.get()
        emails = []
        reg_email = str(system_data['reg_email'])
        emails.append(reg_email)
        system_email = str(system_data['email'])
        emails.append(system_email)
        system_comp = system_data['reg_comp']
        write_str = "<h4>" + zone + " has accepted your system registration request</h4><br>"
        write_str += "<h5>Inspections can now be performed on system: " + system + '</h5>'
        subject = zone + ' Has Accepted Your System Registration Request'

        send_email([reg_email], write_str, subject)
    else:
        system_ref = db.reference('/systems/' + system)
        system_token = str(uuid.uuid4())
        system_ref.update({
            'token': system_token
        })
        system_data = system_ref.get()
        reg_email = str(system_data['reg_email'])
        system_comp = system_data['reg_comp']

        link = get_main_link() + system_comp + '/change-zone/' + \
            system + '/' + system_token

        write_str = "<h3>" + zone + \
                    " has declined your registration request for system #" + system + '</h3><br>'
        write_str += "<h4>They rejected your request for the following reason</h4><br>"
        write_str += '<h5>"' + str(rsp['reason']) + '"</h5>' + '\n'
        write_str += '<h4>Please click <a href="' + link + \
                     '">here</a> to apply to another jurisdiction, or re-register the system if needed</h4>'

        subject = zone + ' Has Rejected Your System Registration Request'

        send_email([reg_email], write_str, subject)

    rem_ref = db.reference('/jurisdictions/' + zone + '/requests/systems/' + str(request_id))
    rem_ref.delete()
    return redirect(url_for('fire_gov_panel.panel', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/comp-register/<comp_id>/req/<request_id>')
def confirm_comp(zone, comp_id, request_id):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)
    click = session.get('click', None)

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))
    try:
        comp_ref = db.reference('/companies/' + comp_id + '/info')
        comp = dict(comp_ref.get())
        personnel = dict(db.reference(
            '/users').order_by_child('comp').equal_to(comp_id).get())
        if (comp_ref == None):
            return redirect(url_for('fire_gov_panel.panel', zone=zone))
    except Exception as e:
        print(e)
        return redirect(url_for('fire_gov_panel.panel', zone=zone))

    return render_template('gov/reg-comp-new.html', request_id=request_id, id=zone, zone=zone, comp_id=comp_id, comp=comp, personnel=personnel)


@panel_blueprint.route('/fire-admin/<zone>/confirm-company', methods=['POST'])
def auth_comp(zone):
    rsp = dict(request.form)
    user_id = session.get('id', None)
    email = session.get('email', None)
    confirm = rsp['confirm']
    company = rsp['comp']
    request_id = rsp['request_id']
    if (confirm == 'yes'):
        comp_ref = db.reference('/companies/' + company)
        comp_data = comp_ref.get()
        comp_zone_ref = db.reference('/companies/' + company + '/info/zones')
        comp_zone_ref.update({
            zone: {
                'date': str(datetime.datetime.now())
            }
        })
        zone_ref = db.reference('/jurisdictions/' + zone + '/companies')
        zone_ref.update({
            company: str(datetime.datetime.now())
        })
        write_str = "<h4>" + str(get_display_name(company)) + \
                    " is now authorized operate in " + zone + '</h4><br>'
        write_str += "<h5>Your company can now perform system inspections and registrations in this jurisdiction</h5>"
        subject = zone + ' Has Authorized ' + str(get_display_name(company))

        comp_emails_raw = list(
            dict(db.reference('/users').order_by_child('comp').equal_to(company).get()).keys())
        comp_emails = []
        for c in comp_emails_raw:
            comp_emails.append(str(c))
        send_email(comp_emails, write_str, subject)
    else:
        write_str = "<h4>Your authorization request was rejected with the following message:" + '</h4><br>'
        write_str += '<h5>"' + str(rsp['reason']) + '"</h5><br>'
        write_str += '<h5>You can email ' + \
                     str(email) + \
                     " To learn more about why your request was rejected</h5>"
        subject = zone + ' Has Rejected Your Authorization Request'

        comp_accts = dict(db.reference('/users').order_by_child('comp').equal_to(company).get())
        comp_emails_keys = list(comp_accts.keys())
        comp_emails = []
        for c in comp_emails_keys:
            if(comp_accts[c]['type'] == 'admin'):
                comp_emails.append(str(comp_accts[c]['email']))
        send_email(comp_emails, write_str, subject)

    rem_ref = db.reference('/jurisdictions/' + zone + '/requests/comp/' + request_id)
    rem_ref.delete()
    return redirect(url_for('fire_gov_panel.panel', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/acct-register/<id>/<token>', methods=['GET'])
def add_acct_confrim_1(zone, id, token):
    acct_ref = db.reference('/users/' + id)
    try:
        account_info = acct_ref.get()
        if (account_info == None):
            return (redirect(url_for('login.login')))
        else:
            acct_token = account_info['token']
            if (acct_token == token):
                session['id'] = id
                session['email'] = account_info['email']
                return (render_template('gov/register-acct.html', user=account_info['email'], zone=zone))
            else:
                return (render_template('msg.html', page="/login", alert="Invalid Auth Token", type="danger"))
    except Exception as e:
        print(e, "error")
        return (render_template('msg.html', page="/login", alert="Invalid Auth Token", type="danger"))


@panel_blueprint.route('/fire-admin/<zone>/reg-add-acct', methods=['POST'])
def add_acct_confrim_2(zone):
    rsp = dict(request.form)
    name = rsp['name']
    phone = str(rsp['phone']).replace('-', '')
    user_id = session.get('id', None)
    email = session.get('email', None)
    token = str(uuid.uuid4())

    pass_hash = pbkdf2_sha256.hash(str(rsp['password']))
    session['token'] = token
    session['name'] = name

    acct_ref = db.reference('/users/' + user_id)
    acct_ref.update({
        'name': name,
        'token': token,
        'time': time.time(),
        'pw': pass_hash,
        'phone': phone
    })

    session['click'] = 'None'
    return redirect(url_for('fire_gov_panel.panel', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/change-2fa-phone', methods=['POST'])
def change_2fa(zone):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)
    session['click'] = 'info-tab'
    rsp = dict(request.form)
    new_phone = str(rsp['phone']).replace('-', '')
    phone_user = db.reference('/users/' + user_id)

    phone_user.update({
        'phone': new_phone
    })

    return redirect(url_for('fire_gov_panel.user_profile', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/change-system', methods=['POST'])
def change_system_status(zone):
    rsp = dict(request.form)
    system = rsp['system']
    change_type = rsp['type']

    if (change_type == 'delete'):
        rem_ref = db.reference('/systems/' + system)
        rem_ref.delete()
    elif (change_type == 'deactivate'):
        change_ref = db.reference('/systems/' + system)
        change_ref.update({
            "active": "no"
        })
    elif (change_type == 'activate'):
        change_ref = db.reference('/systems/' + system)
        change_ref.update({
            "active": "yes"
        })

    return redirect(url_for('fire_gov_panel.view_systems', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/view-system/<system_id>')
def view_system_info(zone, system_id):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))

    system = dict(db.reference('/systems/' + system_id).get())

    return (render_template('gov/view-system-new.html', system=system,
                            system_id=system_id, id=zone))


@panel_blueprint.route('/fire-admin/<zone>/view-comp/<comp_id>')
def view_comp(zone, comp_id):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)
    click = session.get('click', None)
    session['click'] = 'companies-tab'

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))

    try:
        comp = dict(db.reference('/companies/' + comp_id + '/info').get())
        personnel = dict(db.reference(
            '/users').order_by_child('comp').equal_to(comp_id).get())
    except Exception as e:
        print('error here', e)
        return redirect(url_for('fire_gov_panel.panel', zone=zone))

    return render_template('gov/view-comps.html', comp_id=comp_id, id=zone, comp=comp, personnel=personnel, zone=zone)


@panel_blueprint.route('/fire-admin/<zone>/contact-support')
def zone_support(zone):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))

    return render_template('gov/zone-support.html', id=zone, name=name, user_email=email)


@panel_blueprint.route('/fire-admin/<zone>/user-profile')
def user_profile(zone):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))

    user_info = dict(db.reference('/users/' + user_id).get())

    return render_template('gov/view-user.html', id=zone, user_info=user_info)


@panel_blueprint.route('/fire-admin/<zone>/zone-info')
def zone_profile(zone):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)

    try:
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return (redirect(url_for('login.login')))

    users = dict(db.reference(
        '/users').order_by_child('zone').equal_to(zone).get())
    info = db.reference('/jurisdictions/' + zone + '/info').get()
    return render_template('gov/view-zone.html', id=zone, name=name, email=email, users=users, info=info, user_id=user_id)


@panel_blueprint.route('/fire-admin/<zone>/update-logo', methods=['POST'])
def update_logo(zone):

    file = request.files['logo']
    old_filename = secure_filename(file.filename)
    filename = ('/tmp/' + zone + "-logo-" + old_filename)
    mimetype = file.content_type
    file.save(filename)
    optimized_file = resize_photo(filename)
    url = upload_file(optimized_file, mimetype)

    path_logo = '/jurisdictions/' + str(zone) + '/info'
    system = db.reference(path_logo)
    system.update({
        "logo": url
    })
    return redirect(url_for('fire_gov_panel.zone_profile', zone=zone))


@panel_blueprint.route('/fire-admin/<zone>/edit-contact-info', methods=['POST'])
def edit_contact_info(zone):
    rsp = dict(request.form)
    del rsp['csrf_token']
    info_ref = db.reference('/jurisdictions/' + str(zone) + '/info')
    info_ref.update(rsp)
    return redirect(url_for('fire_gov_panel.zone_profile', zone=zone))
