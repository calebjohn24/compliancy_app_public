from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name, upload_file, resize_photo
from import_modules import *
import threading
import queue

storage_client = storage.Client.from_service_account_json(
    "compliancy-app-firebase-adminsdk-bd193-f9c1957881.json")
bucket = storage_client.get_bucket("compliancy-app.appspot.com")

panel_blueprint = Blueprint(
    'fire_admin_panel', __name__, template_folder='templates')


def check_user_token(user, token):
    try:
        path_user = "/users/" + user
        user_data = dict(db.reference(path_user).get())
        print(user_data)
        if ((user_data["token"] == token) and (time.time() - user_data["time"] < 3600)):
            db.reference(path_user).update({"time": time.time()})
            return 0
        else:
            return 1
    except Exception as e:
        print(e, 'err')
        return 1


@panel_blueprint.route('/<comp_name>/admin-panel')
def admin_panel(comp_name):
    st = time.time()
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    print(user)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))

    def get_logs():
        try:
            log_ref = db.reference('/companies/' + comp_name + '/log')
            log_data = dict(log_ref.order_by_child(
                'time').limit_to_last(6).get())
            return log_data
        except Exception as e:
            print(e)
            return {}

    log_que = queue.Queue()
    log_thread = threading.Thread(target=lambda q: q.put(
        get_logs()), args=(log_que,))

    log_thread.start()

    log_thread.join()

    log_result = log_que.get()

    # print(billing_result)

    click = session.get('click', None)
    session['click'] = 'None'

    log_key = db.reference('/companies/' + comp_name +
                           '/billing/log_key').get()

    et = time.time()
    print(et - st)

    info_ref = db.reference('/companies/' + comp_name + "/info")
    info = dict(info_ref.get())

    # return addr, lic, logo, phone, union, website, zones, certs
    return render_template("admin/admin-panel.html", user=user, comp_name=get_display_name(comp_name), id=comp_name,
                           log_key=log_key, click=click, logs=log_result, user_email=user_email, logo=info['logo'])


@panel_blueprint.route('/<comp_name>/admin-panel-reports')
def admin_panel_reports(comp_name):
    st = time.time()
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    print(user)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))

    def get_reports():
        report_ref = db.reference("/reports")
        try:
            reports = dict(report_ref.order_by_child(
                'comp').equal_to(comp_name).get())
            return reports
        except Exception:
            reports = {}
            return reports

    report_que = queue.Queue()
    report_thread = threading.Thread(target=lambda q: q.put(
        get_reports()), args=(report_que,))

    report_thread.start()
    report_thread.join()
    report_result = report_que.get()

    et = time.time()
    print(et - st)

    # return addr, lic, logo, phone, union, website, zones, certs
    return render_template("admin/view-reports.html", user=user, comp_name=get_display_name(comp_name), id=comp_name,
                           reports=report_result)


@panel_blueprint.route('/<comp_name>/admin-panel-systems')
def admin_panel_systems(comp_name):
    st = time.time()
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))
    

    cert_zones = set(dict(db.reference('/companies/' + comp_name + '/info/zones').get()).keys())
    no_cert_zones = set()
    all_zones = set(dict(db.reference('/jurisdictions').get()).keys())

    for az in all_zones:
        check_cert = db.reference('/jurisdictions/' + az + '/info/check_cert').get()
        if (check_cert != 'yes'):
            no_cert_zones.add(az)

    zones_total = no_cert_zones.union(cert_zones)

    systems_final = {}

    system_keys = set()

    for cz in zones_total:
        systems = dict(db.reference(
            '/systems').order_by_child('zone').equal_to(cz).get())

        for h in systems:
            print(system_keys)
            if (h not in system_keys):
                system_keys.add(h)
                systems_final.update({h: systems[h]})

    longitude = (db.reference('/companies/' + comp_name + '/info/long').get())
    latitude = (db.reference('/companies/' + comp_name + '/info/lat').get())

    # return addr, lic, logo, phone, union, website, zones, certs
    return render_template("admin/view-systems.html", user=user, comp_name=get_display_name(comp_name), id=comp_name,
                           system_info=systems_final, longitude=longitude, latitude=latitude)


@panel_blueprint.route('/<comp_name>/admin-panel-billing')
def admin_panel_billing(comp_name):
    st = time.time()
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))

    def get_billing():
        billing_ref = db.reference('/companies/' + comp_name + "/billing")
        billing = dict(billing_ref.get())
        stripe_id = billing['stripe_id']
        card_id = billing['card_id']
        card = stripe.Customer.retrieve_source(
            stripe_id,
            card_id,
        )

        last_4 = str(card.last4)
        card_brand = str(card.brand).capitalize()

        report_price = billing['price']
        report_count = billing['count']
        end_date = billing['end_date']
        start_date = billing['start_date']

        return last_4, card_brand, report_price, report_count, end_date, start_date

    billing_que = queue.Queue()
    billing_thread = threading.Thread(target=lambda q: q.put(
        get_billing()), args=(billing_que,))

    billing_thread.start()

    billing_thread.join()

    billing_result = billing_que.get()

    et = time.time()
    print(et - st)

    # return addr, lic, logo, phone, union, website, zones, certs
    return render_template("admin/view-billing.html", user=user,
                           comp_name=get_display_name(comp_name), id=comp_name, last_4=billing_result[0],
                           card_brand=billing_result[1], report_count=billing_result[3],
                           report_price=billing_result[2], end_date=billing_result[4], start_date=billing_result[5],
                           user_email=user_email)


@panel_blueprint.route('/<comp_name>/admin-panel-comp-info')
def admin_panel_comp_info(comp_name):
    st = time.time()
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    print(user)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))

    photo_token = str(uuid.uuid4())
    db.reference('/users/' + user).update({
        "photo_token":photo_token
    })

    def get_info():
        info_ref = db.reference('/companies/' + comp_name + "/info")
        info = dict(info_ref.get())
        addr = info['addr']
        lic = info['lic']
        logo = info['logo']
        phone = info['phone']
        union = info['union']
        website = info['website']
        try:
            zones = info['zones']
        except Exception:
            zones = {}

        try:
            certs = dict(info['certs'])
        except Exception:
            certs = {}

        certs = (dict(info['certs']))
        return addr, lic, logo, phone, union, website, zones, certs

    info_que = queue.Queue()
    info_thread = threading.Thread(target=lambda q: q.put(
        get_info()), args=(info_que,))

    info_thread.start()

    info_thread.join()

    info_result = info_que.get()

    et = time.time()
    print(et - st)

    # return addr, lic, logo, phone, union, website, zones, certs
    return render_template("admin/view-comp-info.html", photo_token=photo_token, link=get_main_link(), user=user, certs=info_result[7],
                           comp_name=get_display_name(comp_name), id=comp_name,
                           website=info_result[5], addr=info_result[0], lic=info_result[1],
                           logo=info_result[2], phone=info_result[3], union=info_result[4],
                           zones=info_result[6], user_email=user_email)


@panel_blueprint.route('/<comp_name>/admin-panel-user-info')
def admin_panel_user_info(comp_name):
    st = time.time()
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    print(user)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))

    def get_user_data():
        current_user_ref = db.reference("/users/" + user)
        current_user = dict(current_user_ref.get())
        return current_user

    current_user_que = queue.Queue()
    current_user_thread = threading.Thread(target=lambda q: q.put(
        get_user_data()), args=(current_user_que,))

    current_user_thread.start()

    current_user_thread.join()

    current_user = current_user_que.get()

    et = time.time()
    print(et - st)

    # return addr, lic, logo, phone, union, website, zones, certs
    return render_template("admin/view-user-info.html", user=user,
                           comp_name=get_display_name(comp_name), id=comp_name,
                           phone_user=current_user['phone'], name=current_user['name'], user_email=user_email)


@panel_blueprint.route('/<comp_name>/admin-panel-view-techs')
def admin_panel_view_techs(comp_name):
    st = time.time()
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    print(user)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))

    def get_admin_data():
        user_ref = db.reference("/users")
        users = (dict(user_ref.order_by_child(
            'comp').equal_to(comp_name).get()))
        return users

    def get_tech():
        user_ref = db.reference("/users")
        users = (dict(user_ref.order_by_child(
            'comp').equal_to(comp_name).get()))
        return users

    admin_que = queue.Queue()
    admin_data_thread = threading.Thread(target=lambda q: q.put(
        get_admin_data()), args=(admin_que,))

    tech_que = queue.Queue()
    tech_thread = threading.Thread(target=lambda q: q.put(
        get_tech()), args=(tech_que,))

    tech_thread.start()
    admin_data_thread.start()

    tech_thread.join()
    admin_data_thread.join()

    techs = tech_que.get()
    admin_accts = admin_que.get()

    # print(billing_result)

    click = session.get('click', None)
    session['click'] = 'None'

    et = time.time()
    print(et - st)

    # return addr, lic, logo, phone, union, website, zones, certs
    return render_template("admin/view-techs-table.html", user=user,
                           comp_name=get_display_name(comp_name), id=comp_name,
                           admin_users=admin_accts, users=techs, user_email=user_email)


@panel_blueprint.route('/<comp_name>/admin-panel-view-admins')
def admin_panel_view_admins(comp_name):
    st = time.time()
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    print(user)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))

    def get_user_data():
        current_user_ref = db.reference("/users/" + user)
        current_user = dict(current_user_ref.get())
        return current_user

    def get_reports():
        report_ref = db.reference("/reports")
        try:
            reports = dict(report_ref.order_by_child(
                'comp').equal_to(comp_name).get())
            return reports
        except Exception:
            reports = {}
            return reports

    def get_systems():
        system_ref = db.reference("/systems")
        systems = dict(system_ref.get())
        for system_key, system_val in systems.items():
            if (system_val['reg_comp'] != comp_name):
                del systems[system_key]
        return systems

    def get_info():
        info_ref = db.reference('/companies/' + comp_name + "/info")
        info = dict(info_ref.get())
        addr = info['addr']
        lic = info['lic']
        logo = info['logo']
        phone = info['phone']
        union = info['union']
        website = info['website']
        try:
            zones = info['zones']
        except Exception:
            zones = {}

        try:
            certs = dict(info['certs'])
        except Exception:
            certs = {}

        certs = (dict(info['certs']))
        return addr, lic, logo, phone, union, website, zones, certs

    def get_admin_data():
        user_ref = db.reference("/users")
        users = (dict(user_ref.order_by_child(
            'comp').equal_to(comp_name).get()))
        return users

    def get_logs():
        try:
            log_ref = db.reference('/companies/' + comp_name + '/log')
            log_data = dict(log_ref.order_by_child(
                'time').limit_to_last(6).get())
            return log_data
        except Exception as e:
            print(e)
            return {}

    def get_tech():
        user_ref = db.reference("/users")
        users = (dict(user_ref.order_by_child(
            'comp').equal_to(comp_name).get()))
        return users

    def get_billing():
        billing_ref = db.reference('/companies/' + comp_name + "/billing")
        billing = dict(billing_ref.get())
        stripe_id = billing['stripe_id']
        card_id = billing['card_id']
        card = stripe.Customer.retrieve_source(
            stripe_id,
            card_id,
        )

        last_4 = str(card.last4)
        card_brand = str(card.brand).capitalize()

        report_price = billing['price']
        report_count = billing['count']
        end_date = billing['end_date']
        start_date = billing['start_date']

        return last_4, card_brand, report_price, report_count, end_date, start_date

    log_que = queue.Queue()
    log_thread = threading.Thread(target=lambda q: q.put(
        get_logs()), args=(log_que,))

    system_que = queue.Queue()
    system_thread = threading.Thread(target=lambda q: q.put(
        get_systems()), args=(system_que,))

    billing_que = queue.Queue()
    billing_que = queue.Queue()
    billing_thread = threading.Thread(target=lambda q: q.put(
        get_billing()), args=(billing_que,))

    report_que = queue.Queue()
    report_thread = threading.Thread(target=lambda q: q.put(
        get_reports()), args=(report_que,))

    info_que = queue.Queue()
    info_thread = threading.Thread(target=lambda q: q.put(
        get_info()), args=(info_que,))

    current_user_que = queue.Queue()
    current_user_thread = threading.Thread(target=lambda q: q.put(
        get_user_data()), args=(current_user_que,))

    admin_que = queue.Queue()
    admin_data_thread = threading.Thread(target=lambda q: q.put(
        get_admin_data()), args=(admin_que,))

    tech_que = queue.Queue()
    tech_thread = threading.Thread(target=lambda q: q.put(
        get_tech()), args=(tech_que,))

    system_thread.start()
    log_thread.start()
    billing_thread.start()
    report_thread.start()
    info_thread.start()
    current_user_thread.start()
    tech_thread.start()
    admin_data_thread.start()

    system_thread.join()
    log_thread.join()
    billing_thread.join()
    report_thread.join()
    info_thread.join()
    current_user_thread.join()
    tech_thread.join()
    admin_data_thread.join()

    system_result = system_que.get()
    billing_result = billing_que.get()
    report_result = report_que.get()
    info_result = info_que.get()
    current_user = current_user_que.get()
    techs = tech_que.get()
    admin_accts = admin_que.get()
    log_result = log_que.get()

    # print(billing_result)

    click = session.get('click', None)
    session['click'] = 'None'

    log_key = db.reference('/companies/' + comp_name +
                           '/billing/log_key').get()

    et = time.time()
    print(et - st)

    # return addr, lic, logo, phone, union, website, zones, certs
    return render_template("admin/view-admins-table.html", user=user, certs=info_result[7],
                           comp_name=get_display_name(comp_name), id=comp_name,
                           website=info_result[5], addr=info_result[0], lic=info_result[1],
                           logo=info_result[2], phone=info_result[3], union=info_result[4],
                           phone_user=current_user['phone'], log_key=log_key,
                           admin_users=admin_accts, users=techs, reports=report_result, system_info=system_result,
                           zones=info_result[6], name=current_user['name'], last_4=billing_result[
            0], card_brand=billing_result[1], report_count=billing_result[3],
                           report_price=billing_result[2], end_date=billing_result[4], start_date=billing_result[5],
                           click=click, logs=log_result, user_email=user_email)


@panel_blueprint.route('/<comp_name>/admin-panel-support')
def admin_panel_support(comp_name):
    token = session.get('token', None)
    user = session.get('id', None)
    user_email = session.get('email', None)
    if (check_user_token(user, token) == 1):
        return (redirect(url_for('login.login')))

    return render_template("admin/admin-support.html", user=user, id=comp_name, user_email=user_email)


@panel_blueprint.route('/<comp_name>/change-union', methods=['POST'])
def change_union(comp_name):
    rsp = dict(request.form)
    union_status = rsp['union']
    info_ref = db.reference('/companies/' + comp_name + "/info")

    if (union_status == 'yes'):
        info_ref.update({
            'union': 'True'
        })
    else:
        info_ref.update({
            'union': 'False'
        })
    session['click'] = 'profile-tab'
    return (redirect(url_for('fire_admin_panel.admin_panel_comp_info', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/admin-update~<item>', methods=['POST'])
def update_comp_info(comp_name, item):
    request.parameter_storage_class = ImmutableOrderedMultiDict
    rsp = dict((request.form))
    print(rsp)
    info_ref = db.reference('/companies/' + comp_name + "/info")
    if (item == "addr"):
        addr = rsp['addr'] + ' ' + rsp['city'] + \
               ' ' + rsp['state'] + rsp['zip']
        info_ref.update({
            "addr": addr

        })
    elif (item == "phone"):
        info_ref.update({
            "phone": rsp['phone']
        })
    elif (item == "lic"):
        info_ref.update({
            "lic": rsp['lic']
        })
    elif (item == "website"):
        info_ref.update({
            "website": rsp['website']
        })
    session['click'] = 'profile-tab'
    return (redirect(url_for('fire_admin_panel.admin_panel_comp_info', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/edit-dispname', methods=['POST'])
def change_display_name(comp_name):
    request.parameter_storage_class = ImmutableOrderedMultiDict
    rsp = dict((request.form))
    print(rsp)
    name = str(rsp['name'])
    name_ref = db.reference('/companies/' + comp_name + "/info")
    name_ref.update({"display": name})
    session['click'] = 'profile-tab'
    return (redirect(url_for('fire_admin_panel.admin_panel_comp_info', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/add-user', methods=['POST'])
def add_standard_user(comp_name):
    request.parameter_storage_class = ImmutableOrderedMultiDict
    rsp = dict((request.form))
    print(rsp)
    email = str(rsp['email'])
    user_ref = db.reference("/users")
    new_user = user_ref.push({
        "name": 'pending',
        'email': email,
        "time": 0.0,
        'phone': 'pending',
        'count': 0,
        'type': 'tech',
        'comp': comp_name

    })
    info_ref = db.reference('/companies/' + comp_name + "/info")
    info = dict(info_ref.get())
    logo = info['logo']
    main_link = get_main_link()
    write_str = '<h4>Click <a href="' + main_link + comp_name + \
                '/create-user-link/' + new_user.key + \
                '">Here</a> Create Your Technician Account </h4><br>'
    write_str += '<img src="' + logo + '">'
    subject = "Create " + \
              str(get_display_name(comp_name)) + " Technician Account"
    send_email([str(rsp['email'])], write_str, subject)
    session['click'] = 'users-tab'
    return (redirect(url_for('fire_admin_panel.admin_panel_view_techs', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/admin-user-update~<item>', methods=['POST'])
def edit_admin_data(comp_name, item):
    request.parameter_storage_class = ImmutableOrderedMultiDict
    rsp = dict((request.form))
    del rsp['csrf_token']
    print(rsp)
    user_admin = session.get('id', None)
    user_ref = db.reference("/users/" + user_admin)
    if (item == "pw"):
        pw = rsp['pw']
        hash = pbkdf2_sha256.hash(pw)
        user_ref.update({
            "pw": hash
        })
    elif (item == 'number'):
        name = rsp['number']
        user_ref.update({
            "number": rsp['number']
        })
    else:
        name = rsp['name']
        user_ref.update({
            "name": name
        })
    session['click'] = 'profile-tab'
    return (redirect(url_for('fire_admin_panel.admin_panel_user_info', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/add-admin', methods=['POST'])
def add_admin_user(comp_name):
    request.parameter_storage_class = ImmutableOrderedMultiDict
    rsp = dict((request.form))
    print(rsp)
    email = str(rsp['email'])
    user = session.get('email', None)
    if (user != email):
        new_user = db.reference('/users').push({
            'name': 'pending',
            'email': email,
            'time': 0,
            'phone': 'pending',
            'type': 'admin',
            'comp': comp_name

        })
        info_ref = db.reference('/companies/' + comp_name + "/info")
        info = dict(info_ref.get())
        logo = info['logo']
        main_link = get_main_link()
        write_str = '<h4>Click <a href="' + main_link + comp_name + \
                    '/create-admin-link/' + new_user.key + \
                    '">Here</a> Create Your Admin Account </h4><br>'
        write_str += '<img src="' + logo + '">'
        subject = "Create " + \
                  str(get_display_name(comp_name)) + " Admin Account"
        send_email([str(rsp['email'])], write_str, subject)

    return (redirect(url_for('fire_admin_panel.admin_panel_view_admins', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/rem_users~<user_del>')
def rem_users(comp_name, user_del):
    try:
        token = session.get('token', None)
        user = session.get('id', None)
        if (check_user_token(user, token) == 1):
            return (redirect(url_for('fire_admin_login.admin_login', comp_name=comp_name)))
    except Exception as e:
        return (redirect(url_for('fire_admin_login.admin_login', comp_name=comp_name)))
    finally:
        print(user, user_del)
        if (user != user_del):
            user_ref = db.reference("/users/" + user_del)
            user_ref.delete()
        session['click'] = 'users-tab'
        return (redirect(url_for('fire_admin_panel.admin_panel_view_techs', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/rem_admin~<user_del>')
def rem_admin_users(comp_name, user_del):
    try:
        token = session.get('token', None)
        user = session.get('id', None)

        if (check_user_token(user, token) == 1):
            return (redirect(url_for('fire_admin_login.admin_login', comp_name=comp_name)))
    except Exception as e:
        print(e)
        return (redirect(url_for('fire_admin_login.admin_login', comp_name=comp_name)))
    finally:
        if (user != user_del):
            user_ref = db.reference("/users/" + user_del)
            user_ref.delete()
        session['click'] = 'users-tab'
        return (redirect(url_for('fire_admin_panel.admin_panel_view_admins', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/update-logo', methods=['POST'])
def update_logo(comp_name): 
    file = request.files['logo']
    old_filename = secure_filename(file.filename)
    filename = ('/tmp/' + comp_name + "-logo-" + old_filename)
    mimetype = file.content_type
    file.save(filename)
    optimized_file = resize_photo(filename)   
    url = upload_file(optimized_file, mimetype)

    path_logo = '/companies/' + str(comp_name) + '/info'
    system = db.reference(path_logo)
    system.update({
        "logo": url
    })
    return (redirect(url_for('fire_admin_panel.admin_panel_comp_info', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/req-zone')
def disp_zones(comp_name):
    try:
        token = session.get('token', None)
        user = session.get('id', None)
        if (check_user_token(user, token) == 1):
            return (redirect(url_for('fire_admin_login.admin_login', comp_name=comp_name)))
    except Exception as e:
        print(e)
        return (redirect(url_for('fire_admin_login.admin_login', comp_name=comp_name)))

    all_zones_ref = db.reference('/jurisdictions')
    all_zones = set((dict(all_zones_ref.get()).keys()))

    try:
        comp_zones_ref = db.reference(
            '/companies/' + comp_name + '/info/zones')
        comp_zones = set((dict(comp_zones_ref.get()).keys()))
    except Exception as e:
        comp_zones = set({})

    zones = list(all_zones.difference(comp_zones))
    session['click'] = 'profile-tab'
    return render_template('admin/add-zone.html', zones=zones, comp_name=comp_name, id=comp_name)


@panel_blueprint.route('/<comp_name>/admin-add-zone', methods=['POST'])
def add_zone(comp_name):
    rsp = dict(request.form)
    zone = rsp['zone']
    comp_info = dict(db.reference('/companies/' + comp_name + '/info').get())
    comp_requests_ref = db.reference(
        '/jurisdictions/' + zone + '/requests/comp')
    comp_requests_ref.push({
            'id':comp_name,
            'name':comp_info['display'],
            'legal_name':comp_info['legal_name'],
            'lic':comp_info['lic'],
            'addr':str(comp_info['addr']+' '+comp_info['city']+', '+ comp_info['state']+ ' ' + str(comp_info['zip']))

    })

    comp_ref = db.reference('/companies/' + comp_name + '/info/zones')
    comp_ref.update({
        zone: {
            'date': 'pending'
        }
    })

    return (redirect(url_for('fire_admin_panel.admin_panel_comp_info', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/update-cert', methods=['POST'])
def update_cert(comp_name):
    rsp = dict(request.form)
    brand = rsp['brand']
    file = request.files['cert']
    filename = secure_filename(file.filename)
    filename = ('/tmp/' + comp_name + "-cert-" + brand + "-photo.jpg")
    mimetype = file.content_type
    file.save(filename)
    optimized_file = resize_photo(filename)   
    url = upload_file(optimized_file, mimetype)
    cert_ref = db.reference('/companies/' + comp_name + '/info/certs')
    cert_ref.update({
        brand: {
            'img': url
        }
    })
    session['click'] = 'profile-tab'
    os.remove('/tmp/' + comp_name + "-cert-" + brand + "-photo.jpg")
    return (redirect(url_for('fire_admin_panel.admin_panel_comp_info', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/add-cert', methods=['POST'])
def add_cert(comp_name):
    rsp = dict(request.form)
    brand = rsp['brand']
    if (brand != ''):
        file = request.files['cert']
        filename = secure_filename(file.filename)
        filename = ('/tmp/' + comp_name + "-cert-" + brand + "-photo.jpg")
        mimetype = file.content_type
        file.save(filename)
        optimized_file = resize_photo(filename)   
        url = upload_file(optimized_file, mimetype)
        cert_ref = db.reference('/companies/' + comp_name + '/info/certs')
        cert_ref.update({
            brand: {
                'img': url
            }
        })
        os.remove('/tmp/' + comp_name + "-cert-" + brand + "-photo.jpg")
        session['click'] = 'profile-tab'
    return (redirect(url_for('fire_admin_panel.admin_panel_comp_info', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/create-user-link/<user_id>')
def standard_user_setup(comp_name, user_id):
    user = dict(db.reference('/users/' + user_id).get())
    try:
        if (user['name'] == 'pending' and user['time'] == 0 and user['type'] == 'tech'):
            return (render_template('admin/register-acct.html', user_id=user_id, user=user['email'], acct="user",
                                    comp_name=get_display_name(comp_name), comp_id=comp_name))
        else:
            return render_template("msg.html", page='admin-login', type='warning', alert="Account Already Setup")
    except Exception as e:
        print(e)
        return render_template("msg.html", page='/' + comp_name + '/admin-login', type='danger',
                               alert="No Setup Link Has Been Sent to This Email")


@panel_blueprint.route('/<comp_name>/create-admin-link/<user_id>')
def admin_user_setup(comp_name, user_id):
    user = dict(db.reference('/users/' + user_id).get())
    try:
        if (user['name'] == 'pending' and user['time'] == 0 and user['type'] == 'admin'):
            return (render_template('admin/register-acct.html', user_id=user_id, user=user['email'], acct="admin",
                                    comp_name=get_display_name(comp_name), comp_id=comp_name, id=comp_name))
        else:
            return render_template("msg.html", page='/login', type='warning', alert="Account Already Setup")
    except Exception as e:
        print(e)
        return render_template("msg.html", page='/login', type='danger',
                               alert="No Setup Link Has Been Sent to This Email")


@panel_blueprint.route('/<comp_name>/reg-user', methods=['POST'])
def register_user(comp_name):
    rsp = dict(request.form)
    user_id = rsp['id']
    email = rsp['user']
    pw = rsp['password']
    phone = str(rsp['phone']).replace('-', '')
    name = rsp['name']
    icc = rsp['icc']
    if (icc == ""):
        icc = "None"
    state_cert = rsp['state-cert']
    if (state_cert == ""):
        state_cert = "None"

    hash_pw = pbkdf2_sha256.hash(pw)
    token = str(uuid.uuid4())
    db.reference("/users/" + user_id).update({
        "name": name,
        "phone": phone,
        "pw": hash_pw,
        "count": 0,
        "time": time.time(),
        "token": token,
        "icc": icc,
        "state-cert": state_cert
    })
    session['email'] = email
    session['id'] = user_id
    session['token'] = token
    session['name'] = name
    return (redirect(url_for('fire_user_panel.user_panel', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/reg-admin', methods=['POST'])
def register_admin(comp_name):
    rsp = dict(request.form)
    user_id = rsp['id']
    email = rsp['user']
    pw = rsp['password']
    phone = str(rsp['phone']).replace('-', '')
    name = rsp['name']
    hash_pw = pbkdf2_sha256.hash(pw)
    token = str(uuid.uuid4())
    db.reference("/users/" + user_id).update({
        "name": name,
        "phone": phone,
        "pw": hash_pw,
        "time": time.time(),
        "token": token
    })
    session['user'] = email
    session['token'] = token
    session['id'] = user_id
    session['name'] = name
    return (redirect(url_for('fire_admin_panel.admin_panel', comp_name=comp_name)))


@panel_blueprint.route('/<comp_name>/view-system/<system_id>')
def view_system_info(comp_name, system_id):
    try:
        token = session.get('token', None)
        user = session.get('id', None)
        if (check_user_token(user, token) == 1):
            return (redirect(url_for('fire_admin_login.admin_login', comp_name=comp_name)))
    except Exception as e:
        print(e)
        return (redirect(url_for('fire_admin_login.admin_login', comp_name=comp_name)))

    system = dict(db.reference('/systems/' + system_id).get())
    return (render_template('admin/view-system-new.html', id=comp_name,
                            system=system,
                            system_id=system_id))


@panel_blueprint.route('/<comp_name>/user-view/<user>', methods=['GET'])
def view_user(comp_name, user):
    try:
        token = session.get('token', None)
        user_id = session.get('id', None)
        if (check_user_token(user_id, token) == 1):
            return (redirect(url_for('fire_admin_login.admin_login', comp_name=comp_name)))
    except Exception as e:
        print(e)
        return (redirect(url_for('fire_admin_login.admin_login', comp_name=comp_name)))

    bill_time = float(db.reference('/companies/' + comp_name + '/billing/bill_time').get())

    user_info = dict(db.reference('/users/' + user).get())
    reports = dict(db.reference(
        '/reports').order_by_child('user_id').equal_to(user).get())
    systems = dict(db.reference(
        '/systems').order_by_child('user_id').equal_to(user).get())
    log_key = db.reference('/companies/' + comp_name +
                           '/billing/log_key').get()

    user_logs = dict(db.reference('/companies/' + comp_name + '/log/' + log_key).get())

    log_ref = db.reference('/companies/' + comp_name + '/log')
    logs = dict(log_ref.get())

    log_keys = []

    time_keys = []

    for k, v in logs.items():
        time_keys.append(v['time'])

    time_keys.sort()
    time_keys = time_keys[::-1]

    print(time_keys)

    for time_key in time_keys:
        print(time_key)
        for k, v in logs.items():
            print(v, time_key)
            if (v['time'] == time_key):
                log_keys.append(k)

    return (render_template('admin/view-user.html', id=comp_name, user_info=user_info, user=user, bill_time=bill_time,
                            comp_name=comp_name, systems=systems, reports=reports, user_logs=user_logs, logs=logs,
                            log_keys=log_keys))


@panel_blueprint.route('/comp/<comp_name>/photo-cert-upload/<cert>/user/<user_id>/photo-token/<photo_token>', methods=['GET'])
def cert_photo(comp_name, cert, user_id, photo_token):
    user_ref = db.reference('/users/' + user_id)
    try:
        user_data = user_ref.get()
        user_token = user_data['photo_token']
        if(user_token == photo_token):
            return (render_template('admin/cert-photo.html', cert=cert, comp_name=comp_name))
        else:
            return (redirect(url_for('login.login')))
    except Exception as e:
        return (redirect(url_for('login.login')))


@panel_blueprint.route('/<comp_name>/photo-cert-upload/<cert>', methods=['POST'])
def cert_photo_msg(comp_name, cert):
    try:
        file_token = str(uuid.uuid4())
        file = request.files['photo']
        old_filename = secure_filename(file.filename)
        filename = ('tmp/' + comp_name + "-" + file_token + '-' + old_filename)
        mimetype = file.content_type
        file.save(filename)
        optimized_file = resize_photo(filename)   
        url = upload_file(optimized_file, mimetype)
        if(url == "ERROR"):
            success = "no"
            return render_template('base/photo-upload-msg.html', success=success)
        else:
            cert_ref = db.reference('/companies/' + comp_name + '/info/certs/' + cert)
            cert_ref.update({
                "img":url
            })
            success = "yes"
            return (render_template('admin/cert-photo-msg.html', success=success))
    except Exception as e:
        success = "no"
        return (render_template('admin/cert-photo-msg.html', success=success))




@panel_blueprint.route('/<comp_name>/change-zone/<system_id>/<system_token>')
def change_zone_start(comp_name, system_id, system_token):
    try:
        system_ref = db.reference('/systems/' + system_id)
        system_info = system_ref.get()
        if(system_info['token'] == system_token and system_info['zone'] == 'pending'):
            cert_zones = dict(db.reference('/companies/' + comp_name + '/info/zones').get())
            cert_zones_set = set((cert_zones).keys())

            for k in cert_zones.keys():
                if(cert_zones[k]['date'] == 'pending'):
                    cert_zones_set.remove(k)
            
            
            
            no_cert_zones = set()
            all_zones = set(dict(db.reference('/jurisdictions').get()).keys())

            for az in all_zones:
                check_cert = db.reference(
                    '/jurisdictions/' + az + '/info/check_cert').get()
                if (check_cert != 'yes'):
                    no_cert_zones.add(az)

            zones_total = no_cert_zones.union(cert_zones_set)

            zones_total_list = list(zones_total)
            return render_template('base/pick-zone.html', zones=zones_total_list, system_id=system_id)
        else:
            return render_template("msg.html", page='/login', type='success', alert="System Already Re-Zoned")
    except Exception as e:
        print(e)
        return render_template("msg.html", page='/login', type='danger', alert="System Does Not Exist")


@panel_blueprint.route('/send-new-zone-req', methods=['POST'])
def change_zone():
    rsp = dict(request.form)
    zone = rsp['zone']
    system_id = rsp['system_id']

    system_ref = db.reference('/systems/' + system_id)
    system_info = system_ref.get()


    add_ref = db.reference('/jurisdictions/' +
                                   zone + '/requests/systems')
    add_ref.push({
        
            'system':system_id,
            'type': system_info['type'],
            'req_type':'reg',
            'name':system_info['name'],
            'addr':str(system_info['addr']+' '+system_info['city']+', '+ system_info['state']+ ' ' + str(system_info['zip']))
        

    })

    system_ref.update({
        'token':str(uuid.uuid4())
    })



    return render_template("msg.html", page='/login', type='success', alert="New Request Sent To " + zone)
