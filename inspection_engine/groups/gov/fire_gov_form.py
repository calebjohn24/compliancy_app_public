from flask import Blueprint
from inspection_engine.global_modules.global_functions import get_main_link, get_display_name, check_fire_zone, upload_file, resize_photo
from import_modules import *
import threading
import queue

storage_client = storage.Client.from_service_account_json(
    "compliancy-app-firebase-adminsdk-bd193-f9c1957881.json")
bucket = storage_client.get_bucket("compliancy-app.appspot.com")


form_blueprint = Blueprint(
    'fire_gov_question', __name__, template_folder='templates')


def check_user_token(user_id, token):
    try:
        path_user = '/users/' + user_id
        user_data = dict(db.reference(path_user).get())
        if((user_data["token"] == token) and (time.time() - user_data["time"] < 3600)):
            db.reference(path_user).update({"time": time.time()})
            return 0
        else:
            return 1
    except Exception:
        return 1


@form_blueprint.route('/fire-admin/<zone>/forms')
def form_panel(zone):
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
        form_list = db.reference('/jurisdictions/' + zone + '/form').get()
        if(form_list == None):
            form_list = {}
    except Exception as e:
        print(e, "error-form")
        form_list = {}
    
    system_types = list(db.reference('/system_types').get())

    return render_template('gov/form-panel.html', id=zone, logo=logo, forms=form_list, system_types=system_types)

@form_blueprint.route('/fire-admin/<zone>/change-form-system-type', methods=['POST'])
def change_system_type(zone):
    rsp = dict(request.form)
    system_type = rsp['system_type']
    form_id = rsp['form_id']
    db.reference('/jurisdictions/' + zone + '/form/' + form_id).update({
        'system_type':system_type
    })
    return(redirect(url_for('fire_gov_question.form_panel', zone=zone)))


@form_blueprint.route('/fire-admin/<zone>/rem-question', methods=['POST'])
def rem_question(zone):
    rsp = dict(request.form)
    print(rsp)
    rem_q = rsp['question']
    rem_ref = db.reference('/jurisdictions/' + zone + '/questions/' + rem_q)
    rem_ref.delete()
    session['click'] = 'nav-profile-tab'
    form_id = session.get('form_id', None)
    return(redirect(url_for('fire_gov_question.edit_form', zone=zone, form=form_id)))


@form_blueprint.route('/fire-admin/<zone>/edit-form/rem-form-q', methods=['POST'])
def rem_question_form(zone):
    rsp = dict(request.form)
    print(rsp)
    form_id = rsp['form']
    index_val = int(rsp['index'])
    form_ref = db.reference('/jurisdictions/' + zone +
                            '/form/' + form_id + '/questions')
    form = list(form_ref.get())
    form.pop(index_val)
    form_ref.set(form)
    session['click'] = 'form-tab'
    return redirect(url_for('fire_gov_question.edit_form', zone=zone, form=form_id))


@form_blueprint.route('/fire-admin/<zone>/edit-form/form-add-q', methods=['POST'])
def add_question(zone):
    rsp = dict(request.form)
    print(rsp, "resp")
    form_id = rsp['form']
    index_val = int(rsp['index'])
    question_id = rsp['id']
    question_id = str(question_id).replace(' ', '')
    try:
        q_ref = db.reference('/jurisdictions/' + zone +
                             '/questions/' + question_id)
        q = q_ref.get()
        print(q)
        if(q == None or q == ''):
            session['click'] = 'form-tab'
            return redirect(url_for('fire_gov_question.edit_form', zone=zone, form=form_id))
    except Exception as e:
        print(e, "error")
        session['click'] = 'form-tab'
        return redirect(url_for('fire_gov_question.panel', zone=zone))

    form_ref = db.reference('/jurisdictions/' + zone +
                            '/form/' + form_id + '/questions')

    try:
        form = list(form_ref.get())
        form.insert(index_val, question_id)
        form_ref.set(form)
    except Exception as e:
        print(e)
        form = [question_id]
        form_ref.set(form)
    session['click'] = 'form-tab'
    return redirect(url_for('fire_gov_question.edit_form', zone=zone, form=form_id))


@form_blueprint.route('/fire-admin/<zone>/edit-form/change-form-q', methods=['POST'])
def change_question(zone):
    rsp = dict(request.form)
    # print(rsp, "resp")
    index_val = int(rsp['index'])
    question_id = rsp['id']
    form_id = rsp['form']
    question_id = str(question_id).replace(' ', '')
    try:
        q_ref = db.reference('/jurisdictions/' + zone +
                             '/questions/' + question_id)
        q = q_ref.get()
        print(q)
        if(q == None or q == ''):
            session['click'] = 'form-tab'
            return redirect(url_for('fire_gov_panel.panel', zone=zone))
    except Exception as e:
        print(e, "error")
        session['click'] = 'form-tab'
        return redirect(url_for('fire_gov_panel.panel', zone=zone))
    form_ref = db.reference('/jurisdictions/' + zone +
                            '/form/' + form_id + '/questions')
    form = list(form_ref.get())
    form[index_val] = question_id
    form_ref.set(form)
    session['click'] = 'form-tab'
    return redirect(url_for('fire_gov_question.edit_form', zone=zone, form=form_id))


@form_blueprint.route('/fire-admin/<zone>/add-question')
def add_question_tool(zone):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)
    click = session.get('click', None)
    try:
        if(check_user_token(user_id, token) == 1):
            return(redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return(redirect(url_for('login.login')))
    question_uid = str(uuid.uuid4())[:8]
    session['q_id'] = question_uid

    user_ref = db.reference('/users/' + user_id)
    photo_token = str(uuid.uuid4())
    user_ref.update({"photo_token": photo_token})
    return(render_template('gov/add-question-0.html', id=zone, q_id=question_uid, user_id=user_id, photo_token=photo_token, link=get_main_link()))


@form_blueprint.route('/fire-admin/<zone>/add-question-type', methods=['POST'])
def set_question_type(zone):
    question_uid = session.get('q_id', None)
    rsp = dict(request.form)
    del rsp['csrf_token']
    del rsp['dummy']
    doc_label = " "
    img_label = " "
    question = rsp['question']
    del rsp['question']
    img_data = 'none'
    file_data = 'none'

    next_bool = 0
    text_bool = 0
    file_bool = 0
    file_data_bool = 0

    for k, v in rsp.items():
        if(v == 'mul' or v == 'checkbox'):
            next_bool = 1
        elif(v == 'text'):
            text_bool = 1
        elif(v == 'file'):
            file_bool = 1
        elif(k == 'instruct-file-link'):
            if(rsp[k] != ''):
                file_data = rsp[k]
                file_data_bool = 1
                if(rsp['doc-label'] != ''):
                    doc_label = rsp['doc-label']

    try:
        file = request.files['instruct-file-file']
        old_filename = secure_filename(file.filename)
        if(old_filename != '' and file_data_bool == 0):
            filename = ('tmp/' + str(zone)+ '-question-' + str(question_uid) + '-' + old_filename)
            mimetype = file.content_type
            file.save(filename)
            url = upload_file(filename, mimetype)
            print(url)
            if(url != "ERROR"):
                file_data = url
            if(rsp['doc-label'] != ''):
                doc_label = rsp['doc-label']
    except Exception as e:
        raise e
        pass

    try:
        file = request.files['instruct-photo-file']
        old_filename = secure_filename(file.filename)
        print(old_filename)
        if(old_filename != ''):
            filename = ('tmp/' + str(zone)+"-question-" + str(question_uid)+"-"+old_filename)
            mimetype = file.content_type
            file.save(filename)
            optimized_file = resize_photo(filename)
            print(optimized_file)
            url = upload_file(optimized_file, mimetype)
            if(url != "ERROR"):
                print(url)
                img_data = url
            else:
                raise "File Upload Error"
        if(rsp['img-label'] != ''):
            img_label = rsp['img-label']
    except Exception as e:
        raise e
        pass
    
    session['question-create'] = question
    if(next_bool == 0):
        if(text_bool == 1 and file_bool == 1):
            db.reference('/jurisdictions/' + zone + '/questions/' + question_uid).update({
                'question': question,
                'type': {
                    'file': "none",
                    'text': "none"
                },
                'img': {
                    'label': img_label,
                    'data': img_data
                },
                'file': {
                    "label": doc_label,
                    "data": file_data
                }
            })
            q_data = {
                'question': question,
                'type': {
                    'file': "none",
                    'text': "none"
                },
                'img': {
                    'label': img_label,
                    'data': img_data
                },
                'file': {
                    "label": doc_label,
                    "data": file_data
                }
            }
        elif(text_bool == 1 and file_bool == 0):
            db.reference('/jurisdictions/' + zone + '/questions/' + question_uid).update({
                'question': question,
                'type': {
                    'text': "none"
                },
                'img': {
                    'label': img_label,
                    'data': img_data
                },
                'file': {
                    "label": doc_label,
                    "data": file_data
                }
            })
            q_data = {
                'question': question,
                'type': {
                    'text': "none"
                },
                'img': {
                    'label': img_label,
                    'data': img_data
                },
                'file': {
                    "label": doc_label,
                    "data": file_data
                }
            }
        elif(text_bool == 0 and file_bool == 1):
            db.reference('/jurisdictions/' + zone + '/questions/' + question_uid ).update({
                'question': question,
                'type': {
                    'file': "none"
                },
                'img': {
                    'label': img_label,
                    'data': img_data
                },
                'file': {
                    "label": doc_label,
                    "data": file_data
                }
            })
            q_data = {
                'question': question,
                'type': {
                    'file': "none"
                },
                'img': {
                    'label': img_label,
                    'data': img_data
                },
                'file': {
                    "label": doc_label,
                    "data": file_data
                }
            }
            
        if(rsp['code-source'] != "" or rsp['code-title'] != ""):
            if(rsp['code-text'] != ""):
                code_source = rsp['code-source']
                code_title = rsp['code-title']
                code_data = {
                    'type':'text',
                    'value':rsp['code-text']
                }
                db.reference('/jurisdictions/' + zone + '/questions/' + question_uid + '/code').update(
                            {
                                "source":code_source,
                                "title":code_title,
                                "data":code_data
                                
                            }
                )
            else:
                try:
                    photo_token = str(uuid.uuid4())
                    file = request.files['code-img']
                    old_filename = secure_filename(file.filename)
                    code_source = rsp['code-source']
                    code_title = rsp['code-title']
                    if(old_filename != ''):
                        filename = ('tmp/' + str(zone) + "-question-code-" + str(question_uid) +"-" + old_filename)
                        mimetype = file.content_type
                        file.save(filename)
                        optimized_file = resize_photo(filename)   
                        url = upload_file(optimized_file, mimetype)                     
                        code_data = {
                            'type':'img',
                            'value':url
                        }
                        db.reference('/jurisdictions/' + zone + '/questions/' + question_uid + '/code').update(
                            {
                                "source":code_source,
                                "title":code_title,
                                "data":code_data
                            }
                        )
                    else:
                        db.reference('/jurisdictions/' + zone + '/questions/' + question_uid + '/code/').update(
                            {
                                "source":code_source,
                                "title":code_title,
                            }
                        )
                except Exception as e:
                    
                    pass
            
        session['click'] = 'nav-profile-tab'
        form_id = session.get('form_id', None)
        return(redirect(url_for('fire_gov_question.edit_form', zone=zone, form=form_id)))
    else:
        db.reference('/jurisdictions/' + zone + '/questions').update({
            question_uid: {
                'question': question,
                'img': {
                    'label': img_label,
                    'data': img_data
                },
                'file': {
                    "label": doc_label,
                    "data": file_data
                }
            }
        })
        
        if(rsp['code-source'] != "" and rsp['code-title'] != ""):
            if(rsp['code-text'] != ""):
                code_source = rsp['code-source']
                code_title = rsp['code-title']
                code_data = {
                    'type':'text',
                    'value':rsp['code-text']
                }
                db.reference('/jurisdictions/' + zone + '/questions/' + question_uid).update(
                            {
                                "code":{
                                    "source":code_source,
                                    "title":code_title,
                                    "data":code_data
                                }
                            }
                )
            else:
                try:
                    photo_token = str(uuid.uuid4())
                    file = request.files['code-img']
                    old_filename = secure_filename(file.filename)
                    code_source = rsp['code-source']
                    code_title = rsp['code-title']
                    if(old_filename != ''):
                        filename = ('tmp/' + str(zone)+"-question-code-" + str(question_uid)+"-"+old_filename)
                        file.save(filename)
                        mimetype = file.content_type
                        optimized_file = resize_photo(filename)   
                        url = upload_file(optimized_file, mimetype)
                        code_data = {
                            'type':'img',
                            'value':url
                        }
                        db.reference('/jurisdictions/' + zone + '/questions/' + question_uid).update(
                            {
                                "code":{
                                    "source":code_source,
                                    "title":code_title,
                                    "data":code_data
                                }
                            }
                        )
                    else:
                        code_data = db.reference('/jurisdictions/' + zone + '/questions/' + question_uid + '/code/data').get()
                        db.reference('/jurisdictions/' + zone + '/questions/' + question_uid + '/code/').update(
                            {
                                "source":code_source,
                                "title":code_title,
                                "data":code_data
                            }
                        )
                except Exception as e:
                    raise e
                    pass
        
        session['click'] = 'question-tab'
        return(render_template('gov/add-question-1.html', rsp=rsp))


@form_blueprint.route('/fire-admin/<zone>/add-question-resp', methods=['POST'])
def add_question_tool_2(zone):
    q_id = session.get('q_id', None)
    question = session.get('question-create', None)
    q_ref = db.reference('/jurisdictions/' + zone + '/questions/' + q_id)
    q_ref.update({
        'question': question
    })
    q_ref = db.reference('/jurisdictions/' + zone +
                         '/questions/' + q_id + '/type')
    rsp = dict(request.form)
    del rsp['csrf_token']
    if 'file-label' in rsp:
        file_label = rsp['file-label']
        q_ref.update({
            'file': file_label
        })
        del rsp['file-label']
    if 'text-label' in rsp:
        text_label = rsp['text-label']
        q_ref.update({
            'text': text_label
        })
        del rsp['text-label']

    if 'mul' in rsp:
        mul_dict = {
            'mul': {
                'ans': {},
                'pop': {}
            }
        }
        for m in range((int(rsp['mul']))):
            ans_uid = str(uuid.uuid4())[:8]
            key_name = 'mul-name-' + str(m)
            key_color = 'mul-color-' + str(m)
            key_pop = 'mul-popup-' + str(m)
            key_tag = 'mul-tag-' + str(m)
            mul_dict['mul']['ans'].update({
                ans_uid: {
                    'data': rsp[key_name],
                    'color': rsp[key_color]
                }
            })
            if(rsp[key_pop] != ""):
                
                mul_dict['mul']['pop'].update({
                    ans_uid: {
                        'data': rsp[key_pop],
                        'tag':rsp[key_tag]
                    }
                })
        q_ref = db.reference('/jurisdictions/' + zone +
                             '/questions/' + q_id + '/type')
        q_ref.update(
            mul_dict
        )

    if 'check' in rsp:
        check_dict = {
            'check': {
                'ans': {},
                'pop': {}
            }
        }
        for m in range((int(rsp['check']))):
            ans_uid = str(uuid.uuid4())[:8]
            key_name = 'check-name-' + str(m)
            key_color = 'check-color-' + str(m)
            key_pop = 'check-popup-' + str(m)
            key_tag = 'check-tag-' + str(m)
            check_dict['check']['ans'].update({
                ans_uid: {
                    'data': rsp[key_name],
                    'color': rsp[key_color]
                }
            })
            if(rsp[key_pop] != ""):
                check_dict['check']['pop'].update({
                    ans_uid: {
                        'data': rsp[key_pop],
                        'tag':rsp[key_tag]
                    }
                })

        q_ref = db.reference('/jurisdictions/' + zone +
                             '/questions/' + q_id + '/type')
        q_ref.update(
            check_dict
        )
    
    form_id = session.get('form_id', None)
    session['click'] = 'nav-profile-tab'
    return(redirect(url_for('fire_gov_question.edit_form', zone=zone, form=form_id)))


@form_blueprint.route('/fire-admin/<zone>/question-added/<question>')
def success(zone, question):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)
    click = session.get('click', None)
    try:
        if(check_user_token(user_id, token) == 1):
            return(redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return(redirect(url_for('login.login')))

    question_ref = db.reference(
        '/jurisdictions/' + zone + '/questions/' + question)
    question_data = dict(question_ref.get())
    return(render_template('gov/question-success.html', question=question_data))


@form_blueprint.route('/fire-admin/<zone>/rem-form', methods=['POST'])
def rem_form(zone):
    rsp = dict(request.form)
    rem_form = rsp['rem']
    form_ref = db.reference('/jurisdictions/' + zone + '/form/' + rem_form)
    form_ref.delete()
    session['click'] = 'form-tab'
    return redirect(url_for('fire_gov_panel.panel', zone=zone))


@form_blueprint.route('/fire-admin/<zone>/add-form', methods=['POST'])
def add_form(zone):
    rsp = dict(request.form)
    form_name = rsp['form-name']
    form_descrip = rsp['form-descrip']
    system_type = rsp['system_type']
    form_ref = db.reference('/jurisdictions/' + zone + '/form')
    form_uid = str(uuid.uuid4())[:8]
    form_ref.update({
        form_uid: {
            'name': form_name,
            'descrip':form_descrip,
            'system_type': system_type,
            'price':40000
        }
    })
    session['click'] = 'form-tab'
    return redirect(url_for('fire_gov_question.edit_form', zone=zone, form=form_uid))


@form_blueprint.route('/fire-admin/<zone>/edit-form/<form>')
def edit_form(zone, form):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)
    click = session.get('click', None)
    session['form_id'] = form

    try:
        if(check_user_token(user_id, token) == 1):
            return(redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return(redirect(url_for('login.login')))
    
    user_ref = db.reference('/users/' + user_id)
    photo_token = str(uuid.uuid4())
    user_ref.update({"photo_token": photo_token})
    
    question_ref = db.reference('/jurisdictions/' + zone + '/questions')
    question_data = dict(question_ref.get())
    form_ref = db.reference('/jurisdictions/' + zone + '/form/' + form)
    form_data = form_ref.get()
    session['click'] = 'form-tab'
    print(click)

    return(render_template('gov/set-form-tool.html', id=zone, click=click, questions=question_data,  form_id=form, form=form_data))


@form_blueprint.route('/fire-admin/<zone>/view-q/<question_id>')
def edit_question(zone, question_id):
    token = session.get('token', None)
    user_id = session.get('id', None)
    name = session.get('name', None)
    email = session.get('email', None)
    click = session.get('click', None)
    form_id = session.get('form_id', None)
    session['click'] = 'nav-profile-tab'
    try:
        if(check_user_token(user_id, token) == 1):
            return(redirect(url_for('login.login')))
    except Exception as e:
        print(e, "error")
        return(redirect(url_for('login.login')))

    question_ref = db.reference(
        '/jurisdictions/' + zone + '/questions/' + question_id)
    question_data = dict(question_ref.get())
    return(render_template('gov/edit-question-tool.html', id=zone, question_id=question_id, question=question_data, form_id=form_id))


@form_blueprint.route('/fire-admin/<zone>/photo-upload/<photo_type>/question/<question_id>/user/<user_id>/photo-token/<photo_token>')
def upload_photo_phone(zone, photo_type, question_id, user_id, photo_token):
    try:
        user_ref = db.reference('/users/' + user_id)
        user_data = user_ref.get()
        print(user_data)
        if(user_data['photo_token'] == photo_token):
            return render_template('base/photo-upload.html', zone=zone, photo_type=photo_type, question_id=question_id, user_id=user_id)
        else:
            return (redirect(url_for('login.login')))
    except Exception as e:
        return (redirect(url_for('login.login')))


@form_blueprint.route('/fire-admin/<zone>/photo-upload/<photo_type>/question/<question_id>/user/<user_id>/upload', methods=['POST'])
def form_upload_photo(zone, photo_type, question_id, user_id):
    try:
        user_ref = db.reference('/users/' + user_id)
        user_data = user_ref.get()
        file_token = str(uuid.uuid4())
        file = request.files['photo']
        old_filename = secure_filename(file.filename)
        filename = ('tmp/' + zone + "-" + file_token + '-' + old_filename)
        mimetype = file.content_type
        file.save(filename)
        optimized_file = resize_photo(filename)   
        url = upload_file(optimized_file, mimetype)
        if(url == "ERROR"):
            success = "no"
            return render_template('base/photo-upload-msg.html', success=success)
        if(photo_type == "code"):
            path_img = '/jurisdictions/' + str(zone) + '/questions/' + question_id + '/code'
            img_ref = db.reference(path_img)
            img_ref.update({
                'data':{
                    'type': 'img',
                    'value':url
                },
                'source':'',
                'title':''
            })
        elif(photo_type == "instruct"):
            path_img = '/jurisdictions/' + str(zone) + '/questions/' + question_id + '/img/'
            img_ref = db.reference(path_img)
            img_ref.update({
                'data': url
            })
        user_ref = db.reference('/users/' + user_id)
        success = "yes"
    except Exception as e:
        print(e)
        success = "no"
    return render_template('base/photo-upload-msg.html', success=success)
