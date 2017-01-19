import hashlib
from biz.supercode.models import SuperCode

def validate_supercode(supercode):
    h = hashlib.sha256();
    h.update(supercode);
    code = h.hexdigest()
    target = SuperCode.objects.all()[0].code
    return code == target

def update_supercode(newcode):
    SuperCode.objects.all().delete()
    h = hashlib.sha256()
    h.update(newcode)
    code = h.hexdigest()
    c = SuperCode(code=code)
    c.save()

def supercode_exists():
    return SuperCode.objects.count() > 0
