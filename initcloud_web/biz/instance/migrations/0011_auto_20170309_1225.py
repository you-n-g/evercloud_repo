# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0010_instance_assigned'),
    ]

    operations = [
        migrations.RenameField(
            model_name='instance',
            old_name='assigned',
            new_name='assigneduser',
        ),
    ]
