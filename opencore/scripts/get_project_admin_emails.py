username = 'admin'
from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
app=makerequest(app)

from zope.app.component.hooks import setSite
setSite(app.openplans)
#import transaction
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)

cat = app.openplans.portal_catalog

from opencore.content.membership import OpenMembership
mship_type = OpenMembership.portal_type

all_projs = cat(portal_type='OpenProject') #, review_state='public')
#for proj_brain in all_projs:
#    print proj_brain.getId
#print "=" * 70

member_project_map = {}
for proj_brain in all_projs:
    # Cobbled together based on opencore.project.browser.manageteam
    # and opencore.project.browser.team
    team_path = '/'.join(['', 'openplans', 'portal_teams', proj_brain.getId])
    try:
        team = app.unrestrictedTraverse(team_path)
    except AttributeError:
        #print "PROBLEM: No team found at %s" % team_path
        continue
    #proj = proj_brain.getObject()
    active_states=team.getActiveStates()
    mship_brains = cat(highestTeamRole='ProjectAdmin',
                       portal_type='OpenMembership', path=team_path,
                       review_state=active_states,
                       )

    mem_ids = []
    for mbrain in mship_brains:
        if mbrain.highestTeamRole == 'ProjectAdmin':
            # Ok, that's the brain for the OpenMembership.
            # I need the email, which is only on the OpenMember, sigh.
            projects_for_this_member = member_project_map.setdefault(mbrain.getId, [])
            projects_for_this_member.append(proj_brain.getId)



members = cat(portal_type='OpenMember', path='/openplans/portal_memberdata/',
              id=member_project_map.keys())

for mbrain in members:
    print '%s,%s' % (mbrain.getId, mbrain.getEmail)
    # I guess we don't need the project for anything anymore after all.

