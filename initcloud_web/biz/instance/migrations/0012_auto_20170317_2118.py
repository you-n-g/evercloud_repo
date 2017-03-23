# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0011_auto_20170309_1225'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='gpu',
            field=models.BooleanField(default=False, verbose_name='GPU'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='instance',
            name='security_cls',
            field=models.IntegerField(default=0, verbose_name='\u5bc6\u7ea7', choices=[(0, '\u79d8\u5bc6'), (1, '\u673a\u5bc6'), (2, '\u6b63\u5728\u8bbe\u7f6e')]),
            preserve_default=True,
        ),
    ]
