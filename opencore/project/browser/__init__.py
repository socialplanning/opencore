from Products.Five import BrowserView
from opencore.interfaces import IHomePage
from opencore.project import PROJ_HOME
from opencore.project.browser.base import ProjectBaseView
from zExceptions import Redirect

HOME_PAGE_ID = PROJ_HOME
HOME_PAGE_TITLE = 'Project Home'
HOME_PAGE_FILE = 'project_index.html'

class RedirectView(BrowserView):
    """redirect to the project home page url"""

    def __call__(self):
        hp = IHomePage(self.context).home_page
        url = '%s/%s' % (self.context.absolute_url(), hp)
        raise Redirect, url

class TourView(ProjectBaseView):
    """ dummy view for the 1 page tour """






