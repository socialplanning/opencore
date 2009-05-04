from opencore.browser.base import BaseView
import simplejson as json

class ProjectsView(BaseView):
    """
    Simple view that returns a JSON dictionary of the projects within
    which a member is active.  Keys are the project ids, values are
    None (for now).
    """
    def projects_json(self):
        # self.viewedmember should always return a member object b/c
        # this view is only registered on member folders
        member = self.viewedmember()
        proj_brains = self.project_brains_for(member)
        proj_map = dict.fromkeys([p.getId for p in proj_brains])
        proj_json = json.dumps(proj_map, separators=(',', ':'))
        return proj_json
