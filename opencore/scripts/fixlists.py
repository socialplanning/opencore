from zope.event import notify
from zope.app.event.objectevent import ObjectModifiedEvent
from zope.component import getUtility
from Products.listen.interfaces import IListLookup
from Testing.makerequest import makerequest
import transaction
from zope.app.component.hooks import setSite

"""Fixes listen mailing lists that have got purged from the IListLookup
utility.  If an optional argument is provided, it's assumed to be
a log file (from a previous run) from which we read FAILED fixes
to try again.
"""

def fixlist(thelist):
    print "fixing %r" % '/'.join(thelist.getPhysicalPath())
    notify(ObjectModifiedEvent(thelist))

def _get_failures_to_retry(logfile):
    lines = logfile.readlines()
    failures = []
    for line  in lines:
        if line.startswith('FAILED'):
            path = line.split()[-1]
            path = path.strip("!'")
            projname = path.split('/')[3]
            failures.append(projname)
    return failures

def fixall(project_container, retrylog=None):
    if retrylog is not None:
        names = _get_failures_to_retry(retrylog)
    else:
        names = None
    ll = getUtility(IListLookup, context=app.openplans)
    for i, proj in enumerate(project_container.objectValues('OpenProject')):
        if names and proj.getId() not in names:
            continue
        project_container._p_jar.sync()
        try:
            listcontainer = proj['lists']
        except:
            continue
        for ml in listcontainer.objectValues('OpenMailingList'):
            fixlist(ml)
	    if ll._mapping.get(ml.mailto.lower()) is None:
                print "FAILED %r!" % '/'.join(ml.getPhysicalPath())
        transaction.commit()

app = makerequest(app)  # plone stuff barfs without a request.
setSite(app.openplans)  # need this or utility lookups mysteriously fail.
import sys
if len(sys.argv) > 1:
     retrylog = open(sys.argv[1], 'r')
else:
     retrylog = None
fixall(app.openplans.projects, retrylog)
