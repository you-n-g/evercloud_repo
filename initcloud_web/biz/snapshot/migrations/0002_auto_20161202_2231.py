# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('snapshot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='snapshot',
            name='snapshot_id',
            field=models.CharField(default=b'', max_length=255, verbose_name='Snap_id'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='snapshot',
            name='snapshot_type',
            field=models.CharField(default=b'', max_length=255, verbose_name='Type'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='snapshot',
            name='volume_id',
            field=models.CharField(default=b'', max_length=255, verbose_name='Volume'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='snapshot',
            name='id',
            field=models.AutoField(serialize=False, primary_key=True),
            preserve_default=True,
        ),
    ]
