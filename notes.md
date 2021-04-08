 # Running background tasks with celery

 ## Required dependencies
 -celery
 -gevent
 -redis

 ## Set up
 1. celery_settings.py file with settings for celery. It's not actually necessary to have. Code still workes just fine without it
 ```
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Europe/London'
enable_utc = True
 ```

 2. celery_factory.py: celery factory function
 the  `celery.config_from_object('celery_settings')` line is not necessary. Code still workes just fine without it
 ```
from celery import Celery

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.config_from_object('celery_settings')

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

 ```
 -using this celery factory in this way hooks celery up to the flask application, giving it access to the application contexts. 
 So you can then define an email task that accesses a mail object without first creating an application context:
 ```
def send_celery_email(self,message_data):
    #with app.app_context():
    message = Message(subject=message_data['subject'], recipients= [message_data['recipients']], body= message_data['body'])
    mail.send(message)

    #no application context required
 ```

 3. In the configurations for the flask app add in the 2 configurations for flask:
 ```
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
 ```


4.  Instantiate celery object, initialize it and define the tasks
-tasks should have a name, bind=true  
-https://docs.celeryproject.org/en/latest/userguide/tasks.html  
-tasks should have `@celery.task` decorator
 ```
from celery_factory import make_celery
celery = make_celery(app)

@celery.task(name='app.send_celery_email', bind=True)
def send_celery_email(self,message_data):
    #with app.app_context():
    message = Message(subject=message_data['subject'], recipients= [message_data['recipients']], body= message_data['body'])
    mail.send(message)

@celery.task(name='app.reverse', bind=True)
def reverse(self,name):
    return name[::-1]

 ```

5. Call a task
-use the apply_async method to call a task so that you can specify which queue it should be routed to
```
send_celery_email.apply_async(args=[message_data], queue='IO')
```

6. Run a broker
docker-compose.yml file with just the broker:
```
version: "3.7"

services:
    redis:
        image: redis
        ports:
            - 6379:6379

```
```
$ docker-compose up -d

```


7. Run a worker

 base command for running a worker: `celery -A app.celery worker`
1. You want to route your tasks to specific queues 
2. 2 main queues to have: IO queue and a computational queue
-IO tasks: -Q IO --pool=gevent --concurrency=500
-Computational tasks:
```
$celery -A app.celery worker -Q IO --pool=gevent --concurrency=500 --loglevel=info

```
see
https://www.distributedpython.com/2018/10/26/celery-execution-pool/

8. Then run the flask app




## To be investigaed
1. How to setup celery with application factory structure
https://www.distributedpython.com/2018/06/19/call-celery-task-outside-codebase/
2. Unit testing celery
https://www.distributedpython.com/2018/05/01/unit-testing-celery-tasks/
3. dockerise celery-flask-redis application 
https://www.distributedpython.com/2018/06/12/celery-django-docker/
https://www.distributedpython.com/2018/11/15/celery-docker/
https://www.distributedpython.com/2018/10/13/flower-docker/
4. celery reload
https://www.distributedpython.com/2019/04/23/celery-reload/
5. scheduling




