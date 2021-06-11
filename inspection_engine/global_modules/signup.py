from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name
from import_modules import *

signup_blueprint = Blueprint(
    'signup_blueprint', __name__, template_folder='templates')


service_email = 'cajohn0205@gmail.com'


@signup_blueprint.route('/signup')
def signup_start():
    return (render_template('signup/signup-start.html'))



@signup_blueprint.route('/signup-type', methods=['POST'])
def set_signup_type():
    rsp = dict(request.form)

    signup_type = rsp['type']

    if (signup_type == 'comp'):
        session['signup_type'] = 'comp'
        return render_template('signup/comp-signup-0.html')
    elif (signup_type == 'fire-admin'):
        session['signup_type'] = 'fire-admin'
        return render_template('signup/fire-admin-form.html')

@signup_blueprint.route('/fire-admin-form', methods=['POST'])
def submit_fire_admin_form():
    rsp = dict(request.form)
    try:
        name = rsp['name']
        email = rsp['email']
        zone_id = rsp['zone_id']
        del rsp['csrf_token']

        write_str = "<h3>Hi, "+ name + "</h3><br>"
        write_str += '<h3>SentinelFW has received your request for ' + zone_id + \
            ' and a representative in touch with you shortly</h5><br><br><hr><br>'

        write_str += '<img width="75" src="https://storage.googleapis.com/compliancy-app.appspot.com/Logo_text_no_bg.png">'

        subject = "Sentinel Fire Watch Account Request"

        send_email([email], write_str, subject)

        write_str = "<h3>New Fire Admin Account</h3><br>"

        write_str += "<h5>Info:<br>" + str(rsp) + '</h5><br>'

        subject = "New SentinelFW Fire Admin Account"

        send_email([service_email], write_str, subject)
        return render_template("msg.html", page='/home', type='success', alert="Request Sent")

    except Exception as e:
        print(e)
        return render_template("msg.html", page='/signup', type='danger', alert="Your form was not submitted please check your email address and try again")


@signup_blueprint.route('/comp-signup-0', methods=['POST', 'GET'])
def signup_stage_0():
    if(request.method == 'POST'):
        rsp = dict(request.form)
        comp_id = str(rsp['comp_name']).lower()
        comp_id = comp_id.replace(' ', '-')
        comp_id += '-' + str(uuid.uuid4())[:5]
        try:
            now = datetime.datetime.now()
            delt = datetime.timedelta(days=30)
            new_customer = stripe.Customer.create(
                email=rsp['admin_email'],
                phone=rsp['comp_phone'],
                name=rsp['comp_legal_name'],
                description=comp_id,
                address={
                    "line1": rsp['line1'],
                    "line2": rsp['line2'],
                    "city": rsp['city'],
                    "state": rsp['state'],
                    "postal_code": rsp['zip'],
                    "country": "US"
                }

            )
            cust_id = new_customer.id
            addr = rsp['line1'] + ' ' + rsp['line2'] + ' ' + rsp['city'] + ' ' + rsp['state'] + ' ' + rsp['zip']

            comp_dict = {
                comp_id: {
                    'billing': {
                        'count': 0,
                        'start_date': str(now)[:10],
                        'end_date': str(now + delt)[:10],
                        'next_bill_time': int(time.time()) + 2592000,
                        'bill_time': int(time.time()),
                        'price': 40,
                        'tax': 'yes',
                        'stripe_id': cust_id,
                        'trial':'now'
                    },
                    'info': {
                        'addr': addr,
                        'display': rsp['comp_name'],
                        'legal_name': rsp['comp_legal_name'],
                        'lic': rsp['lic'],
                        'phone': rsp['comp_phone'],
                        'website': rsp['website'],
                        'union': 'False'
                    }

                }
            }
            user_dict = {
                'email': rsp['admin_email'],
                'phone': rsp['admin_phone'].replace('-',''),
                'name': rsp['admin_name'],
                'type': 'admin',
                'time': 0,
                'token': 'token',
                'pw': pbkdf2_sha256.hash(rsp['pw'])

            }
            session['user_dict'] = user_dict
            session['comp_id'] = comp_id
            session['comp_dict'] = comp_dict
            print(comp_dict)
            print(user_dict)
        except Exception as e:
            print(e)
            return render_template("msg.html", page='/signup', type='danger', alert="An error ocurred please try again")
    else:
        try:
            comp_dict = session.get('comp_dict', None)
            comp_id = session.get('comp_id', None)
            print(comp_dict[comp_id])
        except Exception as e:
            print(e)
            return(redirect('/signup'))

        return render_template('signup/comp-signup-1.html')


@signup_blueprint.route('/comp-add-card', methods=['POST'])
def signup_stage_1():
    comp_dict = session.get('comp_dict', None)
    comp_id = session.get('comp_id', None)
    rsp = dict(request.form)
    try:
        card = stripe.Customer.create_source(
            comp_dict[comp_id]['billing']['stripe_id'],
            source=rsp['stripe_token'],
        )
        test_charge = stripe.Charge.create(
            amount=int(100),  # $15.00 this time
            currency='usd',
            customer=comp_dict[comp_id]['billing']['stripe_id']
        )
        stripe.Refund.create(
            charge=test_charge.id,
        )
    except Exception as e:
        print(e)
        return render_template("msg.html", page='/signup', type='danger', alert="Your Card was declined")

    comp_dict[comp_id]['billing'].update({
        'card_id':card.id
    })
    # return render_template('signup/comp-signup-2.html')
    return('done')
