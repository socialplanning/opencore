from Products.CMFCore.utils import getToolByName
from Products.remember.utils import log_exc


def pend(self, state_change):
    obj=state_change.object
    try:
        mailhost_tool = getToolByName(obj, "MailHost")
        uid, id, email = obj.UID(), obj.getId(), obj.getEmail()

        url_tool = getToolByName(obj, "portal_url")
        url = "%s/confirm-account?key=%s" % (url_tool(), uid)

        mfrom = url_tool.getPortalObject().getProperty('email_from_address')

        mailhost_tool.send("how are you %s?\ngo here: %s" % (id, url),
                           mto=email,
                           mfrom=mfrom,
                           subject='OpenPlans account registration')
        
    except:
        # write tracebacks because otherwise workflow will swallow exceptions
        log_exc()
        raise

def mship_visibility_changed(self, state_change):
    """
    Keep 'intended_visibility' value in sync w/ the wf state.
    """
    obj = state_change.object
    obj.intended_visibility = state_change.new_state.id

