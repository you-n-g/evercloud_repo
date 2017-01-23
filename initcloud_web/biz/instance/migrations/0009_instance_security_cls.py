# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0008_instance_device_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='security_cls',
            field=models.IntegerField(default=0, verbose_name='\u5bc6\u7ea7', choices=[(0, '\u79d8\u5bc6'), (1, '\u673a\u5bc6')]),
            preserve_default=True,
        ),
    ]
