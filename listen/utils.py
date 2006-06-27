import re

from zope.i18nmessageid import MessageFactory
from zope.schema import ValidationError

_ = MessageFactory("opencore")

regex = re.compile(r'[^A-Za-z0-9_\-\.+]')

class InvalidPrefix(ValidationError):
    __doc__ = _("Only the following characters are allowed in "
                "list address prefixes: alpha-numerics, underscores, "
                "hyphens, periods, and plus signs (i.e. A-Z, a-z, 0-9, "
                "and _-.+ symbols).")

def isValidPrefix(prefix):
    """
    Returns True if the prefix only contains valid email prefix chars.
    """
    match = regex.search(prefix)
    if match is not None:
        raise InvalidPrefix
    return True
    
