from Products.CMFCore.utils import getToolByName

marker = object()

def migrate_membership_roles(self, portal):
    tmtool = getToolByName(portal, 'portal_teams')

    for team_id in tmtool.objectIds(spec='OpenTeam'):
        team = tmtool._getOb(team_id)
        for mship_id in team.objectIds(spec='OpenMembership'):
            mship = team._getOb(mship_id)
            team_roles = getattr(mship, '_team_roles', marker)
            if team_roles is marker:
                # mship possibly created after the new code deployment
                continue
            mship.editTeamRoles(list(team_roles))

            
            
