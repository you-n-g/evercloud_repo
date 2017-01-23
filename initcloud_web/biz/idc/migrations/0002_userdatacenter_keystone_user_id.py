# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('idc', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdatacenter',
            name='keystone_user_id',
            field=models.CharField(default=b'123456', max_length=255, verbose_name='User UUID'),
            preserve_default=True,
        ),
    ]
