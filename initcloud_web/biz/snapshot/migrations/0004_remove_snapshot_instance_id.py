# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('snapshot', '0003_snapshot_instance_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='snapshot',
            name='instance_id',
        ),
    ]
