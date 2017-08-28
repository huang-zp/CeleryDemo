# coding : utf-8
import os
import random
from flask import Flask,request,render_template,session,flash,redirect,url_for, jsonify
from flask_mail import Message, Mail
from celery import Celery
from kombu import serialization
import pickle
serialization.registry._decoders.pop("application/x-python-serialize")

app = Flask(__name__)

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['result_backend'] = 'redis://localhost:6379/0'
app.config['MAIL_SERVER'] = 'smtp.163.com'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = "15518997683@163.com"
app.config['MAIL_PASSWORD'] = "asd123456"
app.config['DEFAULT_MAIL_SENDER'] = '15518997683@163.com'

mail = Mail(app)
app.secret_key = "qwerty"

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['result_backend'])
celery.conf.update(app.config)


@celery.task(bind=True)
def long_task(self):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
        tasks.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html', email=session.get('email', ''))
    message_details = {}
    email = request.form['email']
    session['email'] = email
    message_details['subject'] = 'Hello from Flask'
    message_details['recipients'] = [request.form['email']]
    message_details['body'] = 'This is a test email sent from a background Celery task.'
    # send the email
    # msg = Message('Hello from Flask', recipients=[request.form['email']])
    # msg.body = 'This is a test email sent from a background Celery task.'
    if request.form['submit'] == 'Send':
        # send right away
        send_async_email.delay(message_details)
        flash('Sending email to {0}'.format(email))
    else:
        # send in one minute
        send_async_email.apply_async(args=[message_details], countdown=60)
        flash('An email will be sent to {0} in one minute'.format(email))

    return redirect(url_for('index'))


@celery.task
def send_async_email(message_details):
    """Background task to send an email with Flask-Mail."""
    with app.app_context():
        msg = Message(message_details['subject'],
                      message_details['recipients'])
        print message_details['recipients']
        msg.body = message_details['body']
        mail.send(msg)


if __name__ == '__main__':
    app.run()