"""
Preference view
"""
from OFS.interfaces import IObjectWillBeRemovedEvent
from Products.CMFCore.utils import getToolByName
from opencore.browser.base import BaseView
from Products.Five import BrowserView
from Products.TeamSpace.interfaces import ITeamSpaceTeamRelation
from opencore.interfaces import IProject
from opencore.interfaces.adding import IAddProject
from opencore.browser import formhandler
from opencore.project.browser.view import ProjectPreferencesView
from opencore.tasktracker.featurelet import TaskTrackerFeaturelet
from topp.clockqueue.interfaces import IClockQueue
from topp.featurelets.interfaces import IFeatureletSupporter
from topp.featurelets.interfaces import IFeatureletSupporter
from topp.featurelets.supporter import FeatureletSupporter
from topp.utils import zutils
from zope.app.container.contained import IObjectRemovedEvent
from zope.component import adapter, adapts
from zope.interface import implements
import inspect
import logging
import traceback
import zExceptions


log = logging.getLogger('opencore.project')


class ProjectPreferencesView(ProjectPreferencesView):
    """Place holder"""

class ProjectDeletionView(BaseView):
    
    def _handle_delete(self):
        proj_folder = zutils.aq_iface(self, IAddProject)
        title = self.context.Title()
        proj_id = self.context.getId()
        proj_folder.manage_delObjects([proj_id])
        self.add_status_message("You have permanently deleted '%s' " %title)
        self.redirect("%s/create" %proj_folder.absolute_url())
        return True
    handle_delete = formhandler.button('delete')(_handle_delete)


@adapter(IProject, IObjectWillBeRemovedEvent)
def handle_flet_uninstall(project, event=None):
    supporter = IFeatureletSupporter(project)
    for flet_id in supporter.getInstalledFeatureletIds():
        supporter.removeFeaturelet(flet_id, raise_error=False)

@adapter(IProject, IObjectRemovedEvent)
def delete_team(proj, event=None):
    pt = getToolByName(proj, 'portal_teams')
    # it's a bit inelegant to rely on matching ids, but this is fine
    # as long as we have a 1:1 relation btn teams and projects
    team_id = proj.getId()
    if pt.has_key(team_id):
        pt.manage_delObjects([team_id])

@adapter(IProject, IObjectWillBeRemovedEvent)
def handle_blog_delete(project, event=None):
    pass

class ProjectFeatureletSupporter(FeatureletSupporter):
    adapts(IProject)
    implements(IFeatureletSupporter)

    def removeFeaturelet(self, featurelet, raise_error=True):
        """
        See IFeatureletSupporter.
        """
        name, featurelet=self._fetch_featurelet(featurelet)
        if self.storage.has_key(name):
            if 'raise_error' in inspect.getargspec(featurelet.removePackage)[0]:
                featurelet.removePackage(self.context, raise_error=raise_error)
            else:
                featurelet.removePackage(self.context)
            self.storage.pop(name)
                
