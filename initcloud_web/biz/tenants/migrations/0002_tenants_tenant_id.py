# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenants',
            name='tenant_id',
            field=models.CharField(max_length=36, null=True, verbose_name='id'),
            preserve_default=True,
        ),
    ]
