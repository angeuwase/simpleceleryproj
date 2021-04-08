from flask import Flask, render_template, redirect, url_for
from celery import Celery
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField
import os
from celery_factory import make_celery
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', default='')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', default='')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME', default='')
app.config['MAIL_SUPPRESS_SEND'] = False
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'


celery = make_celery(app)
mail = Mail(app)

@celery.task(name='app.send_celery_email', bind=True)
def send_celery_email(self,message_data):
    #with app.app_context():
    message = Message(subject=message_data['subject'], recipients= [message_data['recipients']], body= message_data['body'])
    mail.send(message)

@celery.task(name='app.reverse', bind=True)
def reverse(self,name):
    return name[::-1]


class MyForm(FlaskForm):
    email = StringField('email')

class Name(FlaskForm):
    name = StringField('email')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = MyForm()

    if form.validate_on_submit():
        email = form.email.data
        message_data = {
            'subject': 'Hi from Flask app',
            'recipients': email,
            'body': 'This is an email sent from the flask app' 
        }
           
        
        #send_celery_email.delay(message_data)
        send_celery_email.apply_async(args=[message_data], queue='IO')



        return 'submitted'
    return render_template('index.html', form=form)



@app.route('/reverse/<name>', methods=['GET', 'POST'])
def process_name(name):

    reverse.apply_async(args=[name], queue='IO')



    return 'i did an async task'






if __name__ == '__main__':

    app.run()