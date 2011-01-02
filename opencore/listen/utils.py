import re

from zope.i18nmessageid import MessageFactory
from zope.schema import ValidationError
from zope.app.component.hooks import getSite

from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces.mailinglist import check_mailto, ManagerMailTo, InvalidMailTo, DuplicateMailTo

_ = MessageFactory("opencore")

invalid_list_prefix_re = re.compile(r'[^\w.-]')

def validatePrefix(prefix):
    suffix = getSuffix()
    check_mailto(prefix + suffix)
    match = invalid_list_prefix_re.search(prefix)
    if match is not None:
        return False
    return True

#XXX: I'm not sure how this is supposed to work. - novalis
def isValidPrefix(prefix):
    """
    Returns True if the prefix only contains valid email prefix chars,
    returns False otherwise
    """
    try:
        result = validatePrefix(prefix)
    except InvalidMailTo:
        return False
    except ManagerMailTo:
        return False
    return result
    
def getSuffix():
    """
    Retrieves the FQDN that is the list address suffix for a site from
    the opencore_properties PropertySheet.  Requires a context object
    from inside the site so the properties tool can be retrieved.
    """
    # use getSite since we've got no other acq hook    
    site = getSite()
    ptool = getToolByName(site, 'portal_properties')
    ocprops = ptool._getOb('opencore_properties')
    return '@' + str(ocprops.getProperty('mailing_list_fqdn').strip())
