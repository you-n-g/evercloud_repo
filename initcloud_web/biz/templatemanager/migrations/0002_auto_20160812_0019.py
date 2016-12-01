# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('templatemanager', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='templatemanager',
            name='template_disksize',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_Disksize'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_flag',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_Flag'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_iso',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_ISO'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_mac',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_Mac'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_memory',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_memoy'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_operatestate',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_OperateState'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_ostype',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_Ostype'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_other',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_Other'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_port',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_port'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_protocol',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_Protocol'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_public',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_Public'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_refcount',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_refcount'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_serverip',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_serverip'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_softwarelist',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_Softwarelist'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_state',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_state'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_vcpu',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_vcpu'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='templatemanager',
            name='template_vmcount',
            field=models.CharField(max_length=60, null=True, verbose_name='Template_vmcount'),
            preserve_default=True,
        ),
    ]
