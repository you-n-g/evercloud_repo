# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Templatemanager',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('deleted', models.BooleanField(default=False, verbose_name='Deleted')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Create Date')),
                ('template_name', models.CharField(max_length=60, verbose_name='Template_Name')),
                ('template_uuid', models.CharField(max_length=60, verbose_name='Template_uuid')),
                ('template_baseuuid', models.CharField(max_length=60, verbose_name='Template_baseuuid')),
                ('template_serverip', models.CharField(max_length=60, verbose_name='Template_serverip')),
                ('template_port', models.CharField(max_length=60, verbose_name='Template_port')),
                ('template_state', models.CharField(max_length=60, verbose_name='Template_state')),
                ('template_refcount', models.CharField(max_length=60, verbose_name='Template_refcount')),
                ('template_vmcount', models.CharField(max_length=60, verbose_name='Template_vmcount')),
                ('template_vcpu', models.CharField(max_length=60, verbose_name='Template_vcpu')),
                ('template_memory', models.CharField(max_length=60, verbose_name='Template_memoy')),
                ('template_disksize', models.CharField(max_length=60, verbose_name='Template_Disksize')),
                ('template_mac', models.CharField(max_length=60, verbose_name='Template_Mac')),
                ('template_operatestate', models.CharField(max_length=60, verbose_name='Template_OperateState')),
                ('template_protocol', models.CharField(max_length=60, verbose_name='Template_Protocol')),
                ('template_ostype', models.CharField(max_length=60, verbose_name='Template_Ostype')),
                ('template_softwarelist', models.CharField(max_length=60, verbose_name='Template_Softwarelist')),
                ('template_other', models.CharField(max_length=60, verbose_name='Template_Other')),
                ('template_flag', models.CharField(max_length=60, verbose_name='Template_Flag')),
                ('template_public', models.CharField(max_length=60, verbose_name='Template_Public')),
                ('template_iso', models.CharField(max_length=60, verbose_name='Template_ISO')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-create_date'],
                'db_table': 'templatemanager',
                'verbose_name': 'Templatemanager',
                'verbose_name_plural': 'Templatemanager',
            },
            bases=(models.Model,),
        ),
    ]
