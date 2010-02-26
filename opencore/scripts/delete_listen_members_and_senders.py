from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.User import UnrestrictedUser
from Testing.makerequest import makerequest
from zope.app.component.hooks import setSite
from Products.listen.content import WriteMembershipList

def find(app, users_or_emails):
    app=makerequest(app)
    setSite(app.openplans)
    newSecurityManager(app.REQUEST, UnrestrictedUser('root', '', [], []).__of__(app))
    cat = app.openplans.portal_catalog
    brains = cat.unrestrictedSearchResults(portal_type = 'Open Mailing List')
    results = [(b.getPath(), b.getObject()) for b in brains]
    for path, ml in sorted(results):
        ml =  WriteMembershipList(ml)
        for astring in users_or_emails:
            if ml.is_allowed_sender(astring):
                print "Removing sender %s from %s" % (astring, path)
                ml.remove_allowed_sender(astring)
            if ml.is_subscribed(astring):
                print "Removing subscriber %s from %s" % (astring, path)
                ml.unsubscribe(astring)

