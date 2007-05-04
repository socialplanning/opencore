from Products.Archetypes.BaseObject import BaseObject
from metadata import addDispatcherToMethod, notifyObjectModified
from metadata import notifyObjectCreated

##################################################
# have Archetypes trigger object modified events
##################################################
BaseObject._processForm_old = BaseObject._processForm
BaseObject._processForm = addDispatcherToMethod(BaseObject._processForm,
                                                notifyObjectModified)

BaseObject.update_old = BaseObject.update
BaseObject.update = addDispatcherToMethod(BaseObject.update,
                                          notifyObjectModified)
BaseObject.edit = BaseObject.update


BaseObject.manage_afterAdd_old = BaseObject.manage_afterAdd
BaseObject.manage_afterAdd = addDispatcherToMethod(BaseObject.manage_afterAdd,
                                                   notifyObjectCreated)

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

def unpatch_class(klass, method_name):
    name = PREFIX + method_name
    delattr(klass, method_name)
    orig_method = getattr(klass, name, None)
    if orig_method is not None:
        setattr(klass, method_name, orig_method)

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
