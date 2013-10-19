"""A quick hack to make lots of opencore projects.
hopefully useful for testing how things scale up.

Run this via zopectl run.
"""

from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
from ZODB.POSException import ConflictError
import random
import sys
import time
import transaction
from DateTime import DateTime

featurelets = ["listen"]
def main(app, proj_id, team_data, settings, descr, logo=None):

    creator = settings.get("info", "creator")
    
    user = app.openplans.acl_users.getUser(creator)
    user = user.__of__(app.openplans.acl_users)
    print "Changing stuff as user", user
    newSecurityManager(None, user)
    app = makerequest(app)
    projfolder = app.openplans.projects


    projfolder.REQUEST.form.update({
        'featurelets': featurelets,
        'workflow_policy': settings.get("preferences", "security_policy"),
        'description': descr,
        'set_flets': 1, # sacrifice a chicken to tell opencore not to ignore our featurelet creation request
        'featurelet_skip_content_init': 1, # but dont try to create featurelet content (e.g. project-discussion list)
        })

    projfolder.REQUEST.set('flet_recurse_flag', None) # sacrifice a goat too

    addview = projfolder.restrictedTraverse('@@create')

    projfolder.REQUEST.form.update({
            'project_title': settings.get("info", "title"),
            'projid': proj_id,
            })
    
    addview.handle_request()

    if addview.errors:
        for key, val in addview.errors.items():
            print "ERROR: %s: %s" % (key, val)
        raise RuntimeError("Project creation failed, see errors above.")
    print "created", proj_id

    projobj = projfolder[proj_id]

    if logo:
        projobj.setLogo(logo)
        logo = projobj.getLogo()
        logo.filename = settings.get("logo", "filename")

    projobj.setLocation(settings.get("info", "location"))
    projobj.getField("creation_date").set(projobj, DateTime(settings.get("info", "created_on")))
    projobj.getField("modification_date").set(projobj, DateTime(settings.get("info", "modified_on")))

    projobj._p_changed = True
    projobj.reindexObject()

    memfolder = app.openplans.portal_memberdata

    from opencore.configuration import ADMIN_ROLES

    team = projobj.getTeams()[0]
    for mdata in team_data['members']:
        print "Importing team member %s" % mdata
        member = memfolder[mdata['user_id']]
        try:
            mship = team.joinAndApprove(mem=member,
                                        made_active_date=mdata['timestamp'],
                                        unlisted=not mdata['listed'])
        except ValueError, e:
            if e.args[0] !=  u'You already have a membership on this project.':
                raise e
            wftool = app.openplans.portal_workflow
            mship = team.getMembershipByMemberId(mdata['user_id'])
            if not mdata['listed']:
                wftool.doActionFor(mship, "make_private")
            mship.made_active_date = DateTime(mdata['timestamp'])
            mship._p_changed = True

        if mdata['role'] == "ProjectAdmin":
            team.setTeamRolesForMember(mdata['user_id'], ADMIN_ROLES)

if __name__ == '__main__':
    main(app)
