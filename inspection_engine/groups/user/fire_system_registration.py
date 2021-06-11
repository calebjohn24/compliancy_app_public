from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name, upload_file, resize_photo
from import_modules import *

storage_client = storage.Client.from_service_account_json(
    "compliancy-app-firebase-adminsdk-bd193-f9c1957881.json")
bucket = storage_client.get_bucket("compliancy-app.appspot.com")


system_register_blueprint = Blueprint(
    'system_register_blueprint', __name__, template_folder='templates')

geolocator = geopy.geocoders.Nominatim(user_agent="compliancy_app")


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


@system_register_blueprint.route('/api/reg_system/start', methods=['POST'])
def start_system_reg():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']
    if(check_user_token(user_id, token) == 0):
        system_id = random.randint(1000000, 9999999)
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

        packet = {
            'systemId': system_id,
            'zones': zones_total_list
        }

        return packet
    else:
        return {'error': 403}


@system_register_blueprint.route('/api/reg_system/system_type', methods=['POST'])
def system_reg_system_type():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']

    if(check_user_token(user_id, token) == 0):

        system_types = db.reference('/system_types').get()
        packet = {
            'systemTypes': list(system_types)
        }

        return packet
    else:
        return {'error': 403}


@system_register_blueprint.route('/api/reg_system/brand', methods=['POST'])
def system_reg_certs():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']

    if(check_user_token(user_id, token) == 0):

        zone = rsp['zoneId']

        cert_req = db.reference(
            '/jurisdictions/' + zone + '/info/check_tech_cert').get()
        if (cert_req == 'yes'):
            certs_dict = db.reference(
                '/companies/' + comp_name + '/info/certs').get()

            certs = list(certs_dict.keys())
        else:
            certs = ['Amerex', 'Ansul', 'Kiddie', 'Protex', 'Pyro-Chem',
                     'Piranha', 'Range-Guard', 'Badger', 'Buckeye']
        packet = {
            'certs': certs,
            'cert_req': cert_req
        }

        return packet
    else:
        return {'error': 403}


@system_register_blueprint.route('/api/reg_system/location_info', methods=['POST'])
def system_reg_location_info():
    rsp = dict(request.json)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']

    if(check_user_token(user_id, token) == 0):

        street_addr = rsp['streetAddr']
        city = rsp['city']
        state = rsp['state']
        zip_code = rsp['zipCode']

        full_addr = street_addr + " " + city + " " + state + " " + zip_code
        location = geolocator.geocode(full_addr)

        if(location == None):
            packet = {
                "success": False,
                "lat": 0.0,
                "long": 0.0
            }

        else:
            try:
                packet = {
                    "success": True,
                    "lat": location.latitude,
                    "long": location.longitude
                }
            except Exception as e:
                packet = {
                    "success": False,
                    "lat": 0.0,
                    "long": 0.0
                }
        return packet
    else:
        return {'error': 403}


@system_register_blueprint.route('/api/reg_system/system_upload', methods=['POST'])
def system_reg_upload():
    # print(request.files)
    # print(request.form)
    rsp = dict(request.form)
    comp_name = rsp['compId']
    user_id = rsp['userId']
    token = rsp['token']

    if(check_user_token(user_id, token) == 0):

        try:
            system_id = rsp['systemId']

            file = request.files['photo']
            old_filename = secure_filename(file.filename)
            filename = ('tmp/' + str(system_id) + '-diagram.jpg')
            mimetype = 'image/jpeg'
            file.save(filename)
            optimized_file = resize_photo(filename)   
            url = upload_file(optimized_file, mimetype)

            system_types = list(db.reference('/system_types').get())

            
            

            system_ref = db.reference('/systems/' + system_id)

            zone = rsp['zoneId']

            user_email = db.reference('/users/' + user_id + '/email').get()
            try:
                next_inspect = int(rsp['inspectDays'])
                if(next_inspect < 1):
                    next_inspect = 30
            except TypeError:
                next_inspect = 30
            
            next_inspect_epoch = next_inspect * 86400


            system_data = {
                'active': 'yes',
                'next_inspect_epoch':next_inspect_epoch,
                'next_inspect':next_inspect,
                'addr': rsp['streetAddr'],
                'brand': rsp['brand'],
                'city': rsp['city'],
                'drawing': url,
                'email': rsp['email'],
                'last_inspect': 'na',
                'last_inspect_epoch': time.time(),
                'lat': rsp['lat'],
                'long': rsp['long'],
                'long': rsp['long'],
                'name': rsp['name'],
                'owner': rsp['owner'],
                'phone': rsp['phone'],
                'reg_comp': comp_name,
                'reg_email': user_email,
                'state': rsp['state'],
                'tag': 'White',
                'type': rsp['systemType'],
                'user_id': user_id,
                'zip': rsp['zipCode'],
                'zone': 'pending',
                'time_stamp':(str(datetime.datetime.now())[:-10])
            }

            system_type = rsp['systemType']

            for sys_type in system_types:
                if(sys_type['id'] == system_type):
                    for props in sys_type['extra_info']:
                        system_data.update({
                            str(props):rsp[str(props)]
                        })
                    


            system_ref.update(system_data)

            zone_accts = db.reference(
                '/users').order_by_child('zone').equal_to(zone).get()
            zone_emails = []
            for accts in zone_accts:
                zone_emails.append(zone_accts[accts]['email'])
            print(zone_accts)
            link = get_main_link() + 'fire-admin/' + zone + \
                '/system-register/' + system_id
            write_str = "<h4>" + get_display_name(
                comp_name) + " (" + comp_name + ") wants to register a new system in your jurisdiction</h4><br>"
            write_str += "<h5>System ID: " + system_id + '</h5><br><br>'
            write_str += '<h4>You can review this request on the home page of your dashboard</h4>'
            subject = "New Fire system has requested to be registered in " + zone
            send_email(zone_emails, write_str, subject)

            add_ref = db.reference('/jurisdictions/' +
                                   zone + '/requests/systems')
            add_ref.push({
                
                    'system':system_id,
                    'type': rsp['systemType'],
                    'req_type':'reg',
                    'name':rsp['name'],
                    'addr':str(rsp['streetAddr']+' '+rsp['city']+', '+ rsp['state']+ ' ' + str(rsp['zipCode']))
                

            })

        except Exception as e:
            print(e)
            print('error')
            return {'success': False}


        log_key = (db.reference('/companies/' +
                                    comp_name + '/billing/log_key').get())

        user_log_ref = db.reference(
            '/companies/' + comp_name + '/log/' + log_key + '/users/' + user_id)
        comp_log_ref = db.reference(
            '/companies/' + comp_name + '/log/' + log_key)
        curr_user_log = dict(user_log_ref.get())
        comp_log = dict(comp_log_ref.get())

        system_comp_count = comp_log['systems'] + 1
        system_user_count = curr_user_log['systems'] + 1

        db.reference('/companies/' + comp_name + '/log/' +
                        log_key + '/users/' + user_id).update({
                            'systems': system_user_count
                        })

        db.reference('/companies/' + comp_name + '/log/' +
                        log_key).update({
                            'systems': system_comp_count
                         })
        return {'success': True}

    else:
        return {'error': 403}
