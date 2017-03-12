# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('instance', '0009_instance_security_cls'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='assigned',
            field=models.ForeignKey(related_name='assign', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
