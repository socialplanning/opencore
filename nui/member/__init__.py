from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.nui.base import BaseView
from opencore.nui.formhandler import OctopoLite, action

class MemberPreferences(BaseView, OctopoLite):

    template = ZopeTwoPageTemplateFile('preferences.pt')

    def _mship_brains_for(self, mem):
        active_states = ['public', 'private']
        user_id = mem.getId()
        query = dict(portal_type='OpenMembership',
                     review_state=active_states,
                     getId=user_id,
                     )
        mships = self.catalogtool(**query)
        return mships

    def _mship_brains(self):
        return self._mship_brains_for(self.context)

    def _project_metadata_for(self, project_id):
        portal = self.portal
        portal_path = portal.absolute_url_path()
        projects_folder = 'projects'
        path = [portal_path, projects_folder, project_id]
        path = '/'.join(path)

        cat = self.catalogtool
        project_info = cat.getMetadataForUID(path)
        return project_info

    def _create_project_dict(self, brain):
        path = brain.getPath()
        elts = path.split('/')
        project_id = elts[-2]
        project_info = self._project_metadata_for(project_id)
        proj_title = project_info['Title']
        proj_id = project_info['getId']

        mship_activated_on = self.pretty_date(brain.made_active_date)

        review_state = brain.review_state
        listed = review_state == 'public'

        return dict(title=proj_title,
                    proj_id=proj_id,
                    since=mship_activated_on,
                    listed=listed,
                    )

    def get_projects_for_user(self):
        mships = self._mship_brains()
        project_dicts = map(self._create_project_dict, mships)
        return project_dicts

    def get_invitations_for_user(self):
        invites = []
        invites.append({'name':'Big Animals'})
        invites.append({'name':'Small Animals'})
        return invites

    def _membership_for_proj(self, proj_id):
        tmtool = self.get_tool('portal_teams')
        team = tmtool.getTeamById(proj_id)
        mem = self.context
        mem_id = mem.getId()
        mship = team._getMembershipByMemberId(mem_id)
        return mship

    def leave_project(self, proj_id):
        """ remove membership by marking the membership object as inactive """
        mship = self._membership_for_proj(proj_id)
        wft = self.get_tool('portal_workflow')
        wft.doActionFor(mship, 'deactivate')

    def change_visibility(self, proj_id):
        """ change whether project members appear in listings """
        mship = self._membership_for_proj(proj_id)
        wft = self.get_tool('portal_workflow')
        cur_state = wft.getInfoFor(mship, 'review_state')
        if cur_state == 'public':
            wft.doActionFor(mship, 'make_private')
        else:
            wft.doActionFor(mship, 'make_public')

    @action('leave')
    def leave_handler(self, targets, fields=None):
        for proj_id in targets:
            a=1
            self.leave_project(proj_id)
        return dict((proj_id, dict(action='delete'))
                    for proj_id in targets)

    @action('default_template', default=True)
    def default_template(self, targets=None, fields=None):
        return self.template()
