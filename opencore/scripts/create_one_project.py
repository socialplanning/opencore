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
from opencore.interfaces.membership import IEmailInvites
from zope.component import getUtility

featurelets = ["listen"]
def main(app, proj_id, team_data, settings, descr, logo=None):

    creator = settings.get("info", "creator")
    
    creator_user = app.openplans.acl_users.getUser(creator)
    
    remove_traces_of_admin = False
    if creator_user is None:
        print "*** No such user %s (creator of project %s)"  % (creator, proj_id)

        for mdata in team_data.get('members', []):
            if mdata['role'] == "ProjectAdmin":
                creator_user = app.openplans.acl_users.getUser(mdata['user_id'])
                assert creator_user is not None, mdata
                break
    if creator_user is None:
        print "****** No suitable admin users found, using site admin"
        creator_user = app.acl_users.getUser("admin")
        creator_user = creator_user.__of__(app.acl_users)
    else:
        creator_user = creator_user.__of__(app.openplans.acl_users)
    # https://github.com/socialplanning/opencore/issues/45
    for mdata in team_data.get('members', []):
        if mdata['user_id'] == creator_user.getId():
            break
    else:
        print "Creator user %s is not a project member" % creator_user
        remove_traces_of_admin = True

    print "Changing stuff as user", creator_user
    newSecurityManager(None, creator_user)
    app = makerequest(app)
    projfolder = app.openplans.projects


    projfolder.REQUEST.form.update({
        'featurelets': [i.strip() for i in settings.get("preferences", "tools").split(",")],
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
        logo.getField("creation_date").set(
            logo, DateTime(settings.get("logo", "created_on")))
        logo.getField("modification_date").set(
            logo, DateTime(settings.get("logo", "modified_on")))
        logo_creator = settings.get("logo", "creator")
        logo.Schema()['creators'].set(logo, (creator,))
        logo.creators = (creator,)
        
    from opencore.interfaces import IHomePage
    IHomePage(projobj).home_page = settings.get("preferences", "homepage")

    projobj.setLocation(settings.get("info", "location"))
    projobj.getField("creation_date").set(projobj, DateTime(settings.get("info", "created_on")))
    projobj.getField("modification_date").set(projobj, DateTime(settings.get("info", "modified_on")))

    projobj._p_changed = True
    projobj.reindexObject()

    memfolder = app.openplans.portal_memberdata

    from opencore.configuration import ADMIN_ROLES
    from opencore.member.subscribers import *

    team = projobj.getTeams()[0]
    for mdata in team_data.get('members', []):
        print "Importing team member %s" % mdata

        try:
            member = memfolder[mdata['user_id']]
        except KeyError:
            print "Could not find user %s" % mdata
            continue #            raise # @@TODO https://github.com/socialplanning/opencore/issues/36

        user = app.openplans.acl_users.getUser(mdata['user_id'])
        user = user.__of__(app.openplans.acl_users)
        newSecurityManager(None, user)
        app = makerequest(app)

        team.join()
        
        newSecurityManager(None, creator_user)
        app = makerequest(app)

        mship = team._getOb(mdata['user_id'])
        wftool = app.openplans.portal_workflow
        transition = [t for t in wftool.getTransitionsFor(mship)
                      if t.get('name') == 'Approve']
        if len(transition):
            transition_id = transition[0]['id']
            wftool.doActionFor(mship, transition_id)
        else:
            print "Skipping membership %s" % mship

        if not mdata['listed']:
            wftool.doActionFor(mship, "make_private")

        if mdata['role'] == "ProjectAdmin":
            team.setTeamRolesForMember(mdata['user_id'], ADMIN_ROLES)

        if mdata.get("local_roles", []):
            projobj.manage_setLocalRoles(mdata['user_id'], mdata['local_roles'])
            
        mship.made_active_date = DateTime(mdata['timestamp'])
        mship._p_changed = True

        reindex_membership_project_ids(mship, None)

    from Products.TeamSpace.exceptions import MemberNotFound
    for mdata in team_data.get('member_invites', []):
        try:
            team.addMember(mdata['user_id'])
        except MemberNotFound:
            print '*** could not find member %s' % mdata['user_id']
            continue
        mship = team._getOb(mdata['user_id'])
        timestamp = DateTime(mdata['timestamp'])
        history = mship.workflow_history
        print "Old", history
        for key in history:
            for entry in history[key]:
                if 'time' in entry:
                    entry['time'] = timestamp
        print "New", history

    for mdata in team_data.get('join_requests', []):
        
        user = app.openplans.acl_users.getUser(mdata['user_id'])
        user = user.__of__(app.openplans.acl_users)
        newSecurityManager(None, user)
        app = makerequest(app)

        team.join()
        
        newSecurityManager(None, creator_user)
        app = makerequest(app)

        mship = team._getOb(mdata['user_id'])
        timestamp = DateTime(mdata['timestamp'])
        history = mship.workflow_history
        print "Old", history
        for key in history:
            for entry in history[key]:
                if 'time' in entry:
                    entry['time'] = timestamp
        print "New", history

    util = getUtility(IEmailInvites)
    for mdata in team_data.get('email_invites', []):
        print mdata, util.addInvitation(mdata['email'], projobj.getId(), 
                                        timestamp=DateTime(mdata['timestamp']))

    from opencore.interfaces.pending_requests import IPendingRequests    
    from zope.component import getMultiAdapter
    from opencore.member.interfaces import IHandleMemberWorkflow

    for mdata in team_data.get('unconfirmed_join_requests', []):
        mem = app.openplans.portal_memberdata[mdata['user_id']]
        assert mem is not None, mdata
        if not IHandleMemberWorkflow(mem).is_unconfirmed():
            import sys
            print >> sys.stderr, "**** member %s has an unconfirmed join request for %s but is confirmed" % (mem, projobj)
            continue
        util = getMultiAdapter((mem, app.openplans.projects), IPendingRequests)
        util.addRequest(projobj.getId(), request_message=mdata['message'])

    creator = settings.get("info", "creator")
    projobj.Schema()['creators'].set(projobj, (creator,))
    projobj.creators = (creator,)

    if remove_traces_of_admin:
        mship = team._getOb(creator_user.getId())
        team.manage_delObjects(ids=[creator_user.getId()])

    projobj.reindexObjectSecurity()
    team.reindexObjectSecurity()



if __name__ == '__main__':
    main(app)
