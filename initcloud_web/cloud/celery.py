#-*-coding=utf-8-*-

from __future__ import absolute_import

import os

from celery import Celery
from celery.schedules import crontab

# Set django env 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'initcloud_web.settings')
from django.conf import settings

# Broker: Celery task message center
# Backend: Message center protocol
app = Celery('cloud',
             broker=settings.BROKER_URL,
             backend='amqp',
             include=['cloud.tasks'])
# Set billing task time 
CELERYBEAT_SCHEDULE = {
    'charge_one_hour_cost': {
        'task': 'cloud.billing_task.charge_one_hour_cost',
        'schedule': crontab(hour="*", minute=1),
    }
}

# Celery global setting
# Serializer format: pickle,json,yaml,msgpack
# Timeout: 3600
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
    CELERY_RESULT_PERSISTENT=True,
    CELERY_ACCEPT_CONTENT=['pickle', 'json', 'msgpack', 'yaml'],
    CELERYBEAT_SCHEDULE=CELERYBEAT_SCHEDULE
)



