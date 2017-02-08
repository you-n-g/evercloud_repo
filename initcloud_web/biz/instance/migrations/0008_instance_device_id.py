# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0007_auto_20161224_1812'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='device_id',
            field=models.TextField(null=True, verbose_name='Enabled Devices', blank=True),
            preserve_default=True,
        ),
    ]
