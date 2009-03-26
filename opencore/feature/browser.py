from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from opencore.feature import feature_project
from opencore.feature import get_featured_project_metadata

class FeatureProjectView(BrowserView):
    """handle posting to feature a new project"""

    def __call__(self):
        if self.request.environ['REQUEST_METHOD'] == 'POST':
            project_id = self.request.form.get('project_id', None)
            if project_id is not None:
                feature_project(project_id)
        portal_url = getToolByName(self.context, 'portal_url')()
        return self.request.response.redirect(portal_url + '/projects')

class LatestFeaturedProjectView(BrowserView):
    """handle querying for the latest featured project"""

    def __call__(self):
        return get_featured_project_metadata()
