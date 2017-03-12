# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('idc', '0002_userdatacenter_keystone_user_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdatacenter',
            name='keystone_user_id',
            field=models.CharField(max_length=255, null=True, verbose_name='User UUID'),
            preserve_default=True,
        ),
    ]
