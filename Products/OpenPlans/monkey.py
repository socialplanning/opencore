from Products.Archetypes.BaseObject import BaseObject

from Products.CMFCore.CatalogTool import _getAuthenticatedUser, \
     _checkPermission, AccessInactivePortalContent
from Products.AdvancedQuery import In, Eq, Le, Ge
from Products.AdvancedQuery.eval import eval as _eval
import logging

logger = logging.getLogger('OpenPlans.monkey')

##################################################
# make MaildropHost work like SecureMailHost
##################################################
try:
    from Products.MaildropHost.MaildropHost import MaildropHost
    from Products.SecureMailHost.SecureMailHost import SecureMailBase
except ImportError:
    MaildropHost = None

PREFIX="_orig_method_"

def patch_class(klass, method_name, new_method):
    name = PREFIX + method_name
    orig_method = getattr(klass, method_name, None)
    if orig_method is not None:
        setattr(klass, name, orig_method)
    setattr(klass, method_name, new_method)
    logger.debug("monkeypatched %s.%s.%s" % (klass.__module__,
                                             klass.__name__, method_name))


def unpatch_class(klass, method_name):
    name = PREFIX + method_name
    delattr(klass, method_name)
    orig_method = getattr(klass, name, None)
    if orig_method is not None:
        setattr(klass, method_name, orig_method)
        logger.debug("restoring  %s.%s.%s" % (klass.__module__,
                                              klass.__name__, method_name))

def alt_send(self, mfrom, mto, body, **kwargs):
    return self._orig_method__send(mfrom, mto, body)

def apply_mailhost_patches():
    # Monkeypatch SecureMailHost compatibility into MaildropHost
    patch_class(MaildropHost, 'secureSend',
                SecureMailBase.secureSend.im_func)
    patch_class(MaildropHost, 'setHeaderOf',
                SecureMailBase.setHeaderOf.im_func)
    patch_class(MaildropHost, 'emailListToString',
                SecureMailBase.emailListToString.im_func)
    patch_class(MaildropHost, 'validateSingleNormalizedEmailAddress',
                SecureMailBase.validateSingleNormalizedEmailAddress.im_func)
    patch_class(MaildropHost, 'validateSingleEmailAddress',
                SecureMailBase.validateSingleEmailAddress.im_func)
    patch_class(MaildropHost, 'validateEmailAddresses',
                SecureMailBase.validateEmailAddresses.im_func)

    # Monkeypatch kwargs into MaildropHost send method
    patch_class(MaildropHost, '_send', alt_send)

def unapply_mailhost_patches():
    # Un-monkeypatch SecureMailHost compatibility from MaildropHost
    unpatch_class(MaildropHost, 'secureSend')
    unpatch_class(MaildropHost, 'setHeaderOf')
    unpatch_class(MaildropHost, 'emailListToString')
    unpatch_class(MaildropHost, 'validateSingleNormalizedEmailAddress')
    unpatch_class(MaildropHost, 'validateSingleEmailAddress')
    unpatch_class(MaildropHost, 'validateEmailAddresses')

    # Restore MaildropHost _send method
    unpatch_class(MaildropHost, '_send')

if MaildropHost is not None:
    apply_mailhost_patches()

def new_evalAdvancedQuery(self,query,sortSpecs=()):
    '''evaluate *query* for 'CatalogTool' and sort results according to *sortSpec*.'''
    query = query._clone()

    # taken from 'CatalogTool.searchResults'
    user = _getAuthenticatedUser(self)
    query &= In('allowedRolesAndUsers',self._listAllowedRolesAndUsers(user))
    if not _checkPermission(AccessInactivePortalContent,self):
        now= self.ZopeTime()
        if 'ValidityRange' in self.Indexes.objectIds():
            query &= Eq('ValidityRange', now)
        else:
            if 'effective' in self.Indexes.objectIds():
                query &= Le('effective',now)
            if 'expires' in self.Indexes.objectIds():            
                query &= Ge('expires',now)
    return _eval(self,query,sortSpecs)


def patch_advanced_query():
    """monkey patch dieter's advanced query to make less assumptions
       about the catalog tool """
    
    try: from Products.CMFCore.CatalogTool import CatalogTool
    except ImportError: CatalogTool= None
    if CatalogTool:
        CatalogTool.evalAdvancedQuery= new_evalAdvancedQuery
        del CatalogTool

patch_advanced_query()

def patch_fileattachment():
    """
    tell the FileAttachment to display image types inline
    """
    from Products.SimpleAttachment.content.file import FileAttachment
    image_mimetypes = ('image/jpeg', 'image/gif', 'image/png')
    new_val = image_mimetypes + FileAttachment.inlineMimetypes
    patch_class(FileAttachment, 'inlineMimetypes', new_val)

patch_fileattachment()

