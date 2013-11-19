"""
A `zopectl run` script that makes message mbox and subscriber csv
exports of ALL mailing lists.  Mostly just for testing.
"""
#from Products.listen.extras import import_export
from Testing.makerequest import makerequest
from AccessControl.SecurityManagement import newSecurityManager
from zope.app.component.hooks import setSite

from opencore.export.export_utils import ProjectExportQueueView
from opencore.export.export_utils import get_status

from opencore.auth.SignedCookieAuthHelper import get_secret
from opencore.utility.interfaces import IProvideSiteConfig
from libopencore.auth import generate_cookie_value
from zope.component import getUtility

SECRET = get_secret()


app = makerequest(app)
portal = app.openplans
setSite(portal)
admin = app.acl_users.getUser('admin').__of__(app.acl_users)
newSecurityManager(None, admin)
qview = ProjectExportQueueView(app.openplans, app.openplans.REQUEST)
qview.vardir = "/opt/backup.openfsm.net/var/backup/"
qview.notify = False

config = getUtility(IProvideSiteConfig)

import simplejson as json
import datetime, time, dateutil.parser
cat = app.openplans.portal_catalog
BASEURL = '/'.join([config.get('deliverance uri'), 'projects'])

proj_id = sys.argv[-1]
project = app.openplans.projects[sys.argv[-1]]

if True:

    newSecurityManager(None, admin)

    team_path = '/'.join(['', 'openplans', 'portal_teams', proj_id])
    team = app.unrestrictedTraverse(team_path)

    active_states=team.getActiveStates()
    mship_brains = cat(highestTeamRole='ProjectAdmin',
                       portal_type='OpenMembership', path=team_path,
                       review_state=active_states,
                       )

    for mbrain in mship_brains:
        if mbrain.highestTeamRole == 'ProjectAdmin':
            mem = portal.acl_users.getUser(mbrain.getId)
            if not mem:
                continue
            mem = mem.__of__(portal.acl_users)
            print "Setting user to %s" % mbrain.getId
            newSecurityManager(None, mem)
            cookie = generate_cookie_value(mbrain.getId, SECRET)
            break
    else:
        print "couldn't find suitable admin user for %s" % proj_id
        cookie = generate_cookie_value("admin", SECRET)

    print "Exporting %s..." % proj_id
    status = get_status(proj_id, context_url='/'.join([BASEURL, proj_id]),
                        cookie=cookie, 
                        features=["wikipages", "mailinglists", "wikihistory"])
    path = qview.export(proj_id, status)
    
    print "Exported %s" % path
    print "=" * 60

