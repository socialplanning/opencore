"""Run this via `zopectl run`.

Fixes catalog ghosts that cause various errors such as
http://trac.openplans.org/errors-openplans/ticket/24
and http://trac.openplans.org/errors-openplans/ticket/19
"""

from Testing.makerequest import makerequest
from AccessControl.User import system
from AccessControl.SecurityManagement import newSecurityManager

def find_dupe_projects(app):
    app = makerequest(app)
    newSecurityManager(app.REQUEST, system.__of__(app))
    cat = app.openplans.portal_catalog
    projects = cat.unrestrictedSearchResults(portal_type='OpenProject')
    broken = []
    for p in projects:
        rid = p.data_record_id_
        path = cat.getpath(rid)
        realpath = '/'.join(p.getObject().getPhysicalPath())
        if path != realpath:
             print "OOPS %r %r" % (path, realpath)
             broken.append(realpath)
	else:
             print "ok %r" % realpath
    if broken:
        print "Projects at weird paths to uncatalog:"
        pprint.pprint(broken)
    else:
        print "Nothing to fix"
        return
    #for path in broken_paths:
    #    cat.uncatalog_object(path)

try:
    app
except NameError:
    print __doc__
else:
    find_dupe_projects(app)
