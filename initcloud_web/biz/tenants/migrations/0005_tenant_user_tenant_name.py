# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0004_tenant_user_default_tenant_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant_user',
            name='tenant_name',
            field=models.CharField(max_length=15, null=True, verbose_name='Tenant Name'),
            preserve_default=True,
        ),
    ]
