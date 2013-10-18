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

BASEURL = '/'.join([config.get('deliverance uri'), 'projects'])

#BASEURL = 'http://team.openplans.org/projects'

cat = app.openplans.portal_catalog

import simplejson as json
import datetime, time, dateutil.parser

import os
try:
    os.unlink("/tmp/unpickle.txt")
except:
    pass

try:
    backup_log = open("%s%s" % (qview.vardir, "log.txt"))
except:
    backup_log = []
backup_log = [json.loads(line) for line in backup_log]
backup_log = dict([(line['project'], line) for line in backup_log])

export_rule = sys.argv[-1]
if export_rule == "skip_existing":
    print "Skipping all existing projects"
elif export_rule == "incremental_wikihistory":
    print "Skipping up-to-date wiki histories"
else:
    export_rule = None
    print "Performing a full export"

for proj_id, proj in app.openplans.projects.objectItems(['OpenProject']):


    last_backup = backup_log.get(proj_id)
    last_backup_time = None
    if last_backup is not None:
        last_backup_time = dateutil.parser.parse(last_backup['datetime'])
        if export_rule == "skip_existing":
            print "Skipping %s (last backup: %s)" % (proj_id, last_backup_time)
            continue

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

    print "Exporting %s..." % proj_id
    features = ["wikipages", "mailinglists", "wikihistory"]
    if last_backup_time is not None and export_rule == "incremental_wikihistory":
        if proj.modified() < last_backup_time - datetime.timedelta(1):
            print "Skipping wiki history (last modified %s, last export %s" % (proj.modified(), last_export_wiki)
            features = ["wikipages", "mailinglists"]

    status = get_status(proj_id, context_url='/'.join([BASEURL, proj_id]),
                        cookie=cookie, 
                        features=features)
    path = qview.export(proj_id, status)

    backup_log[proj_id] = {"project": proj_id,
                           "export": path,
                           "datetime": export_starttime}
    
    print "Exported %s" % path
    print "=" * 60

fp = open("%s%s" % (qview.vardir, "test_log.txt"), 'w')
log = [i for i in backup_log.values()]
log = "\n".join([json.dumps(i) for i in log])
print >> fp, log

