import datetime
import json
import sys
import time
import uuid
import random
import requests
import os
import firebase_admin
from passlib.hash import pbkdf2_sha256
from firebase_admin import credentials
from firebase_admin import db
from flask import Blueprint, render_template, abort
from google.cloud import storage
import pytz
from flask import Flask, flash, request, session, jsonify
from flask_compress import Compress
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.utils import secure_filename
from flask import redirect, url_for
from flask import render_template, send_file
from flask_session import Session
from flask_sslify import SSLify
from werkzeug.datastructures import ImmutableOrderedMultiDict
import atexit
from werkzeug.local import Local, LocalManager
from apscheduler.schedulers.background import BackgroundScheduler
import stripe
import geopy
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

stripe.api_key = "STRIPE_KEY"


def send_email(recipients, message_content, subject_content):
    print(recipients, message_content, subject_content)
    message = Mail(
        from_email='noreply@sentintelfw.com',
        to_emails=list(recipients),
        subject=subject_content,
        html_content=message_content)
    try:
        sg = SendGridAPIClient(
            'SGKEY')
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)
