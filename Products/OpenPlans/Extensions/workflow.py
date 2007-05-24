from Products.CMFCore.utils import getToolByName
from Products.remember.utils import log_exc


def pend(self, state_change):
    obj=state_change.object
    try:
        mailhost_tool = getToolByName(obj, "MailHost")
        uid, id, email = obj.UID(), obj.getId(), obj.getEmail()

        url_tool = getToolByName(obj, "portal_url")
        url = "%s/confirm-account?key=%s" % (url_tool.getPhysicalRoot().absolute_url(), uid)

        mailhost_tool.send("how are you %s?\ngo here: %s" % (id, url),
                           mto=email,
                           mfrom='help@openplans.org',
                           subject='OpenPlans account registration')
        
    except:
        # write tracebacks because otherwise workflow will swallow exceptions
        log_exc()
        raise

