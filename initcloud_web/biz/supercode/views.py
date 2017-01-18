import logging
from django.utils.translation import ugettext_lazy as _
from rest_framework.decorators import api_view
from biz.common.utils import fail, success
from biz.supercode.models import SuperCode
from biz.supercode.utils import validate_supercode, update_supercode


LOG = logging.getLogger(__name__)

@api_view(['POST'])
def update_supercode_view(request):
    old = request.data.get("old")
    new1 = request.data.get("new1")
    new2 = request.data.get("new2")
    if (new1 != new2):
        return fail(msg=_("Inconsistent code"))
    elif (validate_supercode(old)):
        update_supercode(new1)
        return success(msg=_("Supercode changed"))
    else:
        return fail(msg=_("Incorrect supercode"))
