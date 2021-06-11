import json
from firebase_admin import db
from PIL import Image
from import_modules import *

infoFile = open("info.json")
info = json.load(infoFile)
global main_link
main_link = info['main_link']


storage_client = storage.Client.from_service_account_json(
    "compliancy-app-firebase-adminsdk-bd193-f9c1957881.json")
bucket = storage_client.get_bucket("compliancy-app.appspot.com")

def get_main_link():
    return str(main_link)


def get_display_name(comp_name):
    try:
        info_ref = db.reference('/companies/' + comp_name + "/info")
        info = dict(info_ref.get())
        if(info != None):
            display_name = info['display']
    except Exception as e:
        print(e)
        display_name = 'invalid company'
    return str(display_name)


def check_fire_zone(comp_name, zone):
    comp_info_ref = db.reference('/companies/' + comp_name + "/info/zones")
    print(comp_info_ref.get())
    comp_zones = list(dict(comp_info_ref.get()).keys())
    set_comp_zones = set(comp_zones)
    if(zone in set_comp_zones):
        return 0
    else:
        return 1

def resize_photo(filename):
    try:
        img = Image.open(filename)
    except Exception as e:
        raise e
    finally:
        img = Image.open(filename)
        width, height = img.size
        if(width > height):
            if(width > 1280):
                aspect_ratio = float(width)/float(height)
                new_width = 1280
                new_height = int(1280/aspect_ratio)
                new_size = new_width, new_height
                try:
                    img.thumbnail(new_size, Image.ANTIALIAS)
                    img.save(filename)
                    return filename
                except Exception as e:
                    raise e
            else:
                return filename
        elif(height > width):
            if(height > 1280):
                aspect_ratio = float(height)/float(width)
                new_height = 1280
                new_width = int(1280/aspect_ratio)
                new_size = new_width, new_height
                try:
                    img.thumbnail(new_size, Image.ANTIALIAS)
                    img.save(filename)
                    return filename
                except Exception as e:
                    print("Could not create new image")
                    raise e
            else:
                return filename
        else:
            if(width > 1280):
                new_height = 1280
                new_width = 1280
                new_size = new_width, new_height
                try:
                    img.thumbnail(new_size, Image.ANTIALIAS)
                    img.save(filename)
                    return filename
                except Exception as e:
                    print("Could not create new image")
                    raise e
            else:
                return filename
    
                
        
def upload_file(filename, mimetype):
    print(filename)
    blob = bucket.blob(filename)
    d = filename
    d = bucket.blob(d)
    d.upload_from_filename(str(filename), content_type=mimetype)
    url = str(d.public_url)
    img_data = url
    os.remove(filename)
    
    return url