import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


message_content = '<h1>Test Html message</h1><br><h5>Test small text</h5><br><a href="google.com">Click here to view Link</a>'
subject_content = "Test Email"
recipients = ['cajohn0205@gmail.com', 'caleb@cedarrobots.com']


def send_email(message_content, subject_content, recipients):
    message = Mail(
        from_email='noreply@sentintelfw.com',
        to_emails=recipients,
        subject=subject_content,
        html_content=message_content)
    try:
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)
