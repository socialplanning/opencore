from opencore.project.browser.base import ProjectBaseView
from zope.component import getMultiAdapter

class LatestActivityView(ProjectBaseView):
    """
    displays latest activity for a project.
    This is a concept class (sandbox) for the time being
    I think/hope the appropriate architecture will
    emerge from playing with it
    """

    def logo_url(self):
        project_info_view = getMultiAdapter((self.context, self.request),
                                            name='project_info')
        return project_info_view.logo_url()

    def team_manager(self):
        """
        returns whether the member has permission to manage the team
        """
        # XXX this method is deprecated
        # should be replaced with below v
        return self.context.isProjectAdmin()
