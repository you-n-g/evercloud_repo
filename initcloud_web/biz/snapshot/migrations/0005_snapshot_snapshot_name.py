# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('snapshot', '0004_remove_snapshot_instance_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='snapshot',
            name='snapshot_name',
            field=models.CharField(default=b'', max_length=255, verbose_name='Snap_name'),
            preserve_default=True,
        ),
    ]
