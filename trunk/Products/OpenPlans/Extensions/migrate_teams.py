import DateTime

from Products.CMFCore.utils import getToolByName
from Products.OpenPlans.content.team import OpenTeam
from opencore.content.membership import OpenMembership

def setOwnership(obj, owner_info):
    app = obj.getPhysicalRoot()
    uf = app.unrestrictedTraverse(owner_info['path'])
    user = uf.getUser(owner_info['id']).__of__(uf)
    obj.changeOwnership(user)
    obj.manage_setLocalRoles(owner_info['id'], ('Owner',))

def migrate_teams(self):
    out = []
    tmtype = OpenTeam.portal_type
    mshiptype = OpenMembership.portal_type

    tmtool = getToolByName(self, 'portal_teams')
    wftool = getToolByName(self, 'portal_workflow')
    mstool = getToolByName(self, 'portal_membership')

    user_id = mstool.getAuthenticatedMember().getId()

    team_wf = wftool.getWorkflowsFor(tmtype)[0]
    mship_wf = wftool.getWorkflowsFor(mshiptype)[0]
    
    teams = tmtool.objectValues()
    for team in teams:
        out.append('TEAM: %s' % team.getId())
        MIGRATE_TEAM = False
        if team.Type() != tmtype:
            MIGRATE_TEAM = True

        mship_map = {}
        mships = team.objectValues()
        for mship in mships:
            if not MIGRATE_TEAM and \
                   mship.Type() == mshiptype:
                continue
            mship_tm_roles = mship.getTeamRoles()
            mship_wf_state = wftool.getInfoFor(mship, 'review_state')
            mship_id = mship.getId()
            mship_map[mship_id] = (mship_tm_roles, mship_wf_state)
            if not MIGRATE_TEAM:
                team.removeMember(mship_id)
                out.append('-> deleted membership: %s' % mship_id)

        if MIGRATE_TEAM:
            team_id = team.getId()
            team_title = team.Title()
            team_owner_info = team.owner_info()
            team_spaces = team.getBRefs(relationship='TeamSpace Team Relation')
            team_wf_state = wftool.getInfoFor(team, 'review_state')
            
            tmtool.manage_delObjects(ids=[team_id])
            out.append('-> deleted team: %s' % team_id)

            tmtool.invokeFactory(tmtype, team_id,
                                 title=team_title)
            team = tmtool._getOb(team_id)
            setOwnership(team, team_owner_info)
            for space in team_spaces:
                space.addReference(team, relationship='TeamSpace Team Relation')
            out.append('-> created replacement team: %s' % team_id)
            
        for mship_id, mship_info in mship_map.items():
            team.addMember(mship_id, membership_type=mshiptype)
            mship = team.getMembershipByMemberId(mship_id)
            mship.editTeamRoles(mship_info[0])
            wftool.doActionFor(mship, 'activate')
        out.append('')

    return '\n'.join(out)
