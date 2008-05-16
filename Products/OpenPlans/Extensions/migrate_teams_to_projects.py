from Products.CMFCore.utils import getToolByName
from Products.TeamSpace.relations import TeamSpaceTeamRelation


def migrate_teams_to_projects(portal):
    pfolder = portal.projects
    tmtool = getToolByName(portal, 'portal_teams')
    tm_roles = ('ProjectAdmin', 'ProjectMember')
    
    for proj_id in pfolder.objectIds(spec='OpenProject'):
        proj = pfolder._getOb(proj_id)
        teams = proj.getTeams()
        proj_id = proj.getId()
        if len(teams) == 1:
            team = teams[0]
            team_id = team.getId()
            if team_id == proj_id:
                # everything is already cool
                continue

            # copy the team, give it the right name, associate w/ proj
            copy_data = tmtool.manage_copyObjects(ids=[team_id])
            tmtool.manage_pasteObjects(copy_data)
            new_team_id = 'copy_of_%s' % team_id
            tmtool.manage_renameObject(new_team_id, proj_id)
            new_team = tmtool._getOb(proj_id)
            proj.setSpaceTeams(new_team)

        elif len(teams) > 1:
            # record the project membership info
            team_map = {}
            for mem_id in proj.projectMemberIds():
                roles = proj.get_local_roles_for_userid(mem_id)
                roles = [r for r in roles if r in tm_roles]
                team_map[mem_id] = roles

            # create a new team and create the memberships
            team_ids = [tm.getId() for tm in teams]

            if proj_id in team_ids:
                # rename the old one out of the way
                tmtool.manage_renameObject(proj_id, 'old_%s' % proj_id)
            proj._createTeam() # <--- adds a membership that we need to remove
            new_team = tmtool._getOb(proj_id)
            mships = list(new_team.objectIds(spec='OpenMembership'))
            new_team.manage_delObjects(mships)

            new_team.addMembers(team_map.keys())
            for mem_id, roles in team_map.items():
                new_team.setTeamRolesForMember(mem_id, roles)
            proj.setSpaceTeams(new_team)

    # delete the orphaned teams
    relationship = TeamSpaceTeamRelation.relationship
    orphaned = []
    for team in tmtool.getTeams():
        projects = team.getBRefs(relationship=relationship)
        if not projects:
            orphaned.append(team.getId())

    tmtool.manage_delObjects(ids=orphaned)
