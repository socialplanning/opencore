from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from opencore.browser.base import BaseView
from opencore.feature import feature_project
from opencore.feature import get_featured_project_metadata

class FeatureProjectView(BaseView):
    """handle posting to feature a new project"""

    def __call__(self):
        portal_url = getToolByName(self.context, 'portal_url')()
        if self.request.environ['REQUEST_METHOD'] == 'POST':
            project_id = self.request.form.get('project_id', None)
            if project_id is not None:
                feature_project(project_id)
                self.add_status_message(u'Project <a href="%s">%s</a> featured' %
                                        (portal_url + '/projects/' + project_id,
                                         project_id))
        return self.request.response.redirect(portal_url + '/projects')

class LatestFeaturedProjectView(BrowserView):
    """handle querying for the latest featured project"""

    def __call__(self):
        return get_featured_project_metadata()
