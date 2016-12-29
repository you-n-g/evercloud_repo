# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('snapshot', '0002_auto_20161202_2231'),
    ]

    operations = [
        migrations.AddField(
            model_name='snapshot',
            name='instance_id',
            field=models.CharField(default=b'', max_length=255, verbose_name='Instance_id'),
            preserve_default=True,
        ),
    ]
