# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0005_instance_tenant_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='core',
            field=models.IntegerField(default=1, verbose_name='Cores'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='instance',
            name='thread',
            field=models.IntegerField(default=1, verbose_name='Threads'),
            preserve_default=True,
        ),
    ]
