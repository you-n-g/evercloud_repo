# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0008_userprofile_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='operation',
            name='message',
            field=models.CharField(max_length=255, null=True, verbose_name='Message'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='operation',
            name='operation_type',
            field=models.IntegerField(default=0, verbose_name='Operation_type'),
            preserve_default=True,
        ),
    ]
