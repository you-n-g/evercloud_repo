# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0002_tenants_tenant_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tenant_user',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tenant_id', models.CharField(max_length=36, null=True, verbose_name='id')),
                ('user_uuid', models.CharField(max_length=36, null=True, verbose_name='user_id')),
                ('user_id', models.CharField(max_length=36, null=True, verbose_name='user_id')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Create Date')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
