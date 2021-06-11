from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name
from import_modules import *

main_page_blueprint = Blueprint(
    'main_page_blueprint', __name__, template_folder='templates')



@main_page_blueprint.route('/')
@main_page_blueprint.route('/home')
def landing_page():
    return render_template('landing_page.html')
