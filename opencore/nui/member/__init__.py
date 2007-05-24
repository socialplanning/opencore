from opencore.nui.base import BaseView

class YourProjectsView(BaseView):

    def get_projects_for_user(self):
        member = self.userobj()
        id = member.getId()
        if id is None: return []
        projects = member.getProjectListing()
        out = []
        for project in projects:
            roles = ', '.join(project.getTeamRolesForAuthMember())
            teams = project.getTeams()
            for team in teams:
                # eventually this will be 1:1 relationship, project:team
                mship = team.getMembershipByMemberId(id)
                if mship is not None:
                    created = mship.created()

            out.append({'title':project.title, 'role':roles, 'since':created, 'status':'not set'})
        return out

    def get_invitations_for_user(self):
        invites = []
        invites.append({'name':'Big Animals'})
        invites.append({'name':'Small Animals'})
        return invites

