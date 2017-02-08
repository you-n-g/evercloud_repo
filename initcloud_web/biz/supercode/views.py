from django.utils.translation import ugettext_lazy as _
from rest_framework.decorators import api_view
from rest_framework.response import Response
from biz.common.utils import fail, success
from biz.supercode.models import SuperCode
from biz.supercode.utils import validate_supercode, update_supercode, supercode_exists


@api_view(['GET', 'POST'])
def update_supercode_view(request):
    if request.method == "GET":
        return Response(supercode_exists())
    else:
        old = request.data.get("old")
        new1 = request.data.get("new1")
        new2 = request.data.get("new2")
        if (new1 != new2):
            return fail(msg=_("Inconsistent code"))
        elif (not supercode_exists() or validate_supercode(old)):
            update_supercode(new1)
            return success(msg=_("Supercode changed"))
        else:
            return fail(msg=_("Incorrect supercode"))
