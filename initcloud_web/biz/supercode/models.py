from django.db import models

class SuperCode(models.Model):
    code = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = "supercode"

