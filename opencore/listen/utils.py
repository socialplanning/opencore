import re

from zope.i18nmessageid import MessageFactory
from zope.schema import ValidationError
from zope.app.component.hooks import getSite

from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces.mailinglist import check_mailto

_ = MessageFactory("opencore")

regex = re.compile(r'[^A-Za-z0-9_\-\.+]')

class InvalidPrefix(ValidationError):
    __doc__ = _("Only the following characters are allowed in "
                "list address prefixes: alpha-numerics, underscores, "
                "hyphens, periods, and plus signs (i.e. A-Z, a-z, 0-9, "
                "and _-.+ symbols).")

def isValidPrefix(prefix):
    """
    Returns True if the prefix only contains valid email prefix chars,
    raises an InvalidPrefix exception otherwise.
    """
    # use getSite since we've got no other acq hook
    suffix = getSuffix()
    check_mailto(prefix + suffix)

    match = regex.search(prefix)
    if match is not None:
        raise InvalidPrefix
    return True
    
def getSuffix():
    """
    Retrieves the FQDN that is the list address suffix for a site from
    the opencore_properties PropertySheet.  Requires a context object
    from inside the site so the properties tool can be retrieved.
    """
    # use threadlocal site to hook into acquisition context
    site = getSite()
    ptool = getToolByName(site, 'portal_properties')
    ocprops = ptool._getOb('opencore_properties')
    return '@' + str(ocprops.getProperty('mailing_list_fqdn').strip())
