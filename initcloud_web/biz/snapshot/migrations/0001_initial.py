# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Snapshot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('snapshotname', models.CharField(max_length=15, verbose_name='Role')),
                ('datacenter', models.IntegerField(default=0, verbose_name='Result')),
                ('deleted', models.BooleanField(default=False, verbose_name='Deleted')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Create Date')),
            ],
            options={
                'ordering': ['-create_date'],
                'db_table': 'snapshot',
                'verbose_name': 'Snapshot',
                'verbose_name_plural': 'Snapshot',
            },
            bases=(models.Model,),
        ),
    ]
