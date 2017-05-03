from django.db import models

class VirDesktopAction(models.Model):
    """Model class for storing action status

    Attributes:
        id: primary key of this table
        vm_id: the id of virtural desktop
        create_date: create date of each record
        state: the current status of this action record
    """
    id = models.AutoField(primary_key=True)
    vm_id = models.CharField(max_length=128, null=False)
    # product_id = models.CharField(max_length=32, null=False)
    create_date = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=32, null=False)

