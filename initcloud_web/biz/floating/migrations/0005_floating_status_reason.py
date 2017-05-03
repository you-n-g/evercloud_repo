# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('floating', '0004_floating_ip_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='floating',
            name='status_reason',
            field=models.CharField(max_length=255, null=True, verbose_name='Status Reason', blank=True),
            preserve_default=True,
        ),
    ]
