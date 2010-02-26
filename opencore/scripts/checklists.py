from zope.component import getUtility
from Products.listen.interfaces import IListLookup
from Testing.makerequest import makerequest
import time
from zope.app.component.hooks import setSite


def checkall(project_container):
    ll = getUtility(IListLookup, context=app.openplans)
    mlcount = 0
    for i, proj in enumerate(project_container.objectValues('OpenProject')):
        try:
            listcontainer = proj['lists']
        except:
            continue
        for ml in listcontainer.objectValues('OpenMailingList'):
            mlcount += 1
	    if ll._mapping.get(ml.mailto.lower()) is None:
                print "FAILED %r!" % '/'.join(ml.getPhysicalPath())
    print "done with %d lists" % mlcount


app = makerequest(app)  # plone stuff barfs without a request.
setSite(app.openplans)  # need this or utility lookups mysteriously fail.
print time.asctime()
checkall(app.openplans.projects)
print
