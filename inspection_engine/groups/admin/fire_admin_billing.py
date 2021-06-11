from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name
from import_modules import *

billing_blueprint = Blueprint(
    'fire_admin_billing_blueprint', __name__, template_folder='templates')


def monthly_log():
    month = 2592000
    print('billing....')
    companies = dict(db.reference('/companies').get())

    for comp in companies:
        bill_time = companies[comp]['billing']['bill_time']
        comp_name = comp
        curr_time = time.time()
        if (curr_time - bill_time >= month):
            now = datetime.datetime.now()
            delt = datetime.timedelta(days=30)
            old_log_key = db.reference('/companies/' + comp_name + '/billing/log_key').get()
            new_log = db.reference('/companies/' + comp_name + '/log').push({
                'systems': 0,
                'reports': 0,
                'time': time.time(),
                'start_date': str(now)[:10],
                'end_date': str(now + delt)[:10],
                'tags': {
                    'red': 0,
                    'yellow': 0,
                    'white': 0
                }
            })

            new_log_key = new_log.key

            user_dict = {}

            users = dict(db.reference('/users').order_by_child('comp').equal_to(comp_name).get())

            for user in users:
                if(users[user]['type'] == 'tech'):
                    tmp = {
                        user: {
                            'systems': 0,
                            'reports': 0,
                            'name': users[user]['name'],
                            'tags': {
                                'red': 0,
                                'yellow': 0,
                                'white':0
                            }
                        }
                    }
                    user_dict.update(tmp)
            db.reference('/companies/' + comp_name + '/log/' + new_log_key).update({
                'users':user_dict
            })
            db.reference('/companies/' + comp_name + '/billing').update({
                'log_key': new_log_key,
                'next_bill_time': int(time.time()) + month,
                'bill_time': int(time.time()),
                'start_date': str(now)[:10],
                'end_date': str(now + delt)[:10]
            })

    
    systems = db.reference('/systems').get()
    for system in systems:
        #print(system)
        try:
            current_system = systems[system]
            last_inspect = current_system['last_inspect_epoch']
            next_inspect = current_system['next_inspect_epoch']

            curr_time = time.time()
            if(curr_time - last_inspect >= next_inspect):

                
                zone = current_system['zone']
                if(zone != 'pending'):
                    req_ref = db.reference('/jurisdictions/' + zone + '/requests')
                    current_requests = req_ref.get()

                    if('past_due' in current_requests):
                        if(system not in current_requests['past_due']):
                            req_ref = db.reference('/jurisdictions/' + zone + '/requests/past_due')
                            req_ref.update({
                                system:{
                                    'type': current_system['type'],
                                    'name':current_system['name'],
                                    'addr':str(current_system['addr']+' '+current_system['city']+', '+ current_system['state']+ ' ' + str(current_system['zip']))
                                }
                            })
                            
                            write_str = "<h4>Your "+ current_system['brand'] + ' '+ current_system['type'] +" System (ID #"+ system +")is past due for an inspection"
                            write_str += 'Your system was last inspected @ ' + \
                                        current_system['last_inspect'] + '. ' + \
                                'and needs to be re-inspected every ' + str(current_system['next_inspect']) + " days</h4><br>  " + "\n"

                            write_str += '<h6>Please Contact a ' + zone + ' Fire Marshal' + \
                                ' If You Have Any Questions</h6><br>' + '\n'
                            subject = 'Your System Is Past Due For Inspection'
                            emails = []
                            emails.append(system['email'])
                            send_email(emails, write_str, subject)
                    else:
                        req_ref = db.reference('/jurisdictions/' + zone + '/requests/past_due')
                        req_ref.update({
                            system:{
                                'type': current_system['type'],
                                'name':current_system['name'],
                                'email':current_system['email'],
                                'phone':current_system['phone'],
                                'addr':str(current_system['addr']+' '+current_system['city']+', '+ current_system['state']+ ' ' + str(current_system['zip']))
                            }
                        })
                        

                        write_str = "<h4>Your "+ current_system['brand'] + ' '+ current_system['type'] +" System (ID #"+ system +")is past due for an inspection"
                        write_str += 'Your system was last inspected @ ' + \
                                    current_system['last_inspect'] + '. ' + \
                            'and needs to be re-inspected every ' + str(current_system['next_inspect']) + " days</h4><br>  " + "\n"

                        write_str += '<h6>Please Contact a ' + zone + ' Fire Marshal' + \
                            ' If You Have Any Questions</h6><br>' + '\n'
                        subject = 'Your System Is Past Due For Inspection'
                        emails = []
                        emails.append(system['email'])
                        send_email(emails, write_str, subject)

                


        except Exception as e:
            #print(e)
            pass
        
    
            

    print('Done')



@billing_blueprint.route('/<comp_name>/update-card', methods=['POST'])
def update_card(comp_name):
    request.parameter_storage_class = ImmutableOrderedMultiDict
    rsp = dict((request.form))
    try:
        billing_ref = db.reference('/companies/' + comp_name + "/billing")
        billing = dict(billing_ref.get())
        stripe_id = billing['stripe_id']
        old_card_id = billing['card_id']

        new_card = stripe.Customer.create_source(
            stripe_id,
            source=str(rsp['stripe_token']),
        )
        new_card_id = new_card.id
        billing_ref.update({
            "card_id": new_card_id
        })
        stripe.Customer.delete_source(
            stripe_id,
            old_card_id,
        )
    except Exception as e:
        print(e)
        return(render_template('admin/card-error.html', comp_name=get_display_name(comp_name), error='Card Declined Please Try Again'))
    return(redirect(url_for('fire_admin_panel.admin_panel_billing', comp_name=comp_name)))
