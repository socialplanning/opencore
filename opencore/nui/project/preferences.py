"""
Preference view
"""
from OFS.interfaces import IObjectWillBeRemovedEvent
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.TeamSpace.interfaces import ITeamSpaceTeamRelation
from opencore.interfaces import IProject
from opencore.interfaces.adding import IAddProject
from opencore.nui import formhandler
from opencore.nui.project.view import ProjectPreferencesView
from opencore.tasktracker.featurelet import TaskTrackerFeaturelet
from topp.clockqueue.interfaces import IClockQueue
from topp.featurelets.interfaces import IFeatureletSupporter
from topp.utils import zutils
from zope.app.container.contained import IObjectRemovedEvent
from zope.component import adapter
import logging
import zExceptions
import traceback


log = logging.getLogger('opencore.project')


class ProjectPreferencesView(ProjectPreferencesView):

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
        supporter.removeFeaturelet(flet_id)

#@adapter(IProject, IObjectWillBeRemovedEvent)
@adapter(ITeamSpaceTeamRelation, IObjectWillBeRemovedEvent)
def queue_delete_team(obj, event=None):
    # this is a miserable hack due to references being deleted via old
    # hooks rather than by events. it is implemented with the hope
    # that some day if we are still using this code, it will be in a
    # different form

    project = obj

    #conditional temporary hack
    if ITeamSpaceTeamRelation.providedBy(obj):
        team = project.getTargetObject()
        team_ids = [team.getId()]
    else:
        team_ids = [team.getId() for team in project.getTeams()]

    # deleting the by triggering off of the reference creates a
    # chicken v. egg issue due to old manage_delete methods. we want
    # to queue this up to take away the team at a later date

    if len(team_ids):
        proj_folder = zutils.aq_iface(project, IAddProject)
        IClockQueue(proj_folder).add_job(delete_team, ids=team_ids)

def delete_team(context, request=None, ids=None):
    pt = getToolByName(context, 'portal_teams')
    try:
        pt.manage_delObjects(ids)
    except zExceptions.BadRequest:
        e = traceback.format_exc()
        log.info(e)
        return e

@adapter(IProject, IObjectWillBeRemovedEvent)
def handle_blog_delete(project, event=None):
    pass

@adapter(IProject, IObjectRemovedEvent)
def kick_cache(project, event=None):
    pass
