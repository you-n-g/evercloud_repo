# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0003_tenant_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant_user',
            name='default_tenant_id',
            field=models.CharField(max_length=36, null=True, verbose_name='default_tenant_id'),
            preserve_default=True,
        ),
    ]
