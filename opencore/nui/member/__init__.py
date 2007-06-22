from opencore.nui.base import BaseView

class MemberPreferences(BaseView):

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

