# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('snapshot', '0002_auto_20170425_1112'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='snapshot',
            table='snapshot',
        ),
    ]
