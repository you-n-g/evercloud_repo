# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0006_auto_20161220_1236'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='instance',
            name='thread',
        ),
        migrations.AddField(
            model_name='instance',
            name='socket',
            field=models.IntegerField(default=1, verbose_name='Sockets'),
            preserve_default=True,
        ),
    ]
