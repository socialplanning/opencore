"""
Preference view
"""
from opencore.browser import formhandler
from opencore.browser.base import _
from opencore.interfaces.workflow import IReadWorkflowPolicySupport
from opencore.project.browser.base import ProjectBaseView

import logging

log = logging.getLogger('opencore.project.browser.preferences')

from opencore.framework.editform import EditView
class ProjectPreferencesView(ProjectBaseView, EditView):

    def save(self, request):
        if not 'update' in request.form:
            return

        # possibly this filtering should happen on the IEditable object?
        new_form = self.filter_params(request)
        old_form = request.form
        request.form = new_form
        from opencore.framework.editform import IEditable
        IEditable(self.context).save(request)
        request.form = old_form

        self.add_status_message('Your changes have been saved.')

    def filter_params(self, request):
        allowed_params = set(['__initialize_project__', 'update', 'set_flets',
                              'project_title', 'description', 'logo', 'workflow_policy',
                              'featurelets', 'home-page',
                              'location',])
        new_form = {}
        for k in allowed_params:
            if k in request.form:
                if 'project_title' == k:
                    # Aarrgghh!! #*!&% plone snoops into the request, and reads the form variables directly,
                    # so we have to set the form variables with the same names as the schema
                    new_form['title'] = request.form[k]
                else:
                    new_form[k] = request.form[k]
        return new_form

    def error_handler(self, errors):
        self.errors = errors
        self.add_status_message(_(u'psm_correct_errors_below',
                                  u'Please correct the errors indicated below.'))

    def validate(self, request):
        return {}

    def redirect(self, request):
        return request.response.redirect(self.context.absolute_url())


from opencore.interfaces.adding import IAddProject
from topp.utils import zutils
class ProjectDeletionView(ProjectBaseView):
    
    def _handle_delete(self):
        proj_folder = zutils.aq_iface(self, IAddProject)
        title = self.context.Title()
        proj_id = self.context.getId()
        proj_folder.manage_delObjects([proj_id])
        self.add_status_message("You have permanently deleted '%s' " %title)
        # link to account page
        account_url = '%s/account' % self.member_info['folder_url']
        self.redirect(account_url)
        return True
    handle_delete = formhandler.button('delete')(_handle_delete)


## XXX event subscribers do *not* belong in a browser module
from topp.featurelets.supporter import FeatureletSupporter

from OFS.interfaces import IObjectWillBeRemovedEvent
from opencore.interfaces import IProject
from topp.featurelets.interfaces import IFeatureletSupporter
from zope.component import adapter
@adapter(IProject, IObjectWillBeRemovedEvent)
def handle_flet_uninstall(project, event=None):
    supporter = IFeatureletSupporter(project)
    for flet_id in supporter.getInstalledFeatureletIds():
        supporter.removeFeaturelet(flet_id, raise_error=False)

from Products.CMFCore.utils import getToolByName
from zope.app.container.contained import IObjectRemovedEvent
@adapter(IProject, IObjectRemovedEvent)
def delete_team(proj, event=None):
    pt = getToolByName(proj, 'portal_teams')
    # it's a bit inelegant to rely on matching ids, but this is fine
    # as long as we have a 1:1 relation btn teams and projects
    team_id = proj.getId()
    if pt.has_key(team_id):
        pt.manage_delObjects([team_id])

from opencore.interfaces.membership import IEmailInvites
from zope.component import getUtility
@adapter(IProject, IObjectRemovedEvent)
def delete_email_invites(proj, event=None):
    invite_util = getUtility(IEmailInvites, context=proj)
    invite_util.removeAllInvitesForProject(proj.getId())

@adapter(IProject, IObjectWillBeRemovedEvent)
def handle_blog_delete(project, event=None):
    pass

from zope.interface import implements
from zope.component import adapts
import inspect
class ProjectFeatureletSupporter(FeatureletSupporter):
    adapts(IProject)
    implements(IFeatureletSupporter)

    def removeFeaturelet(self, featurelet, raise_error=True):
        """
        See IFeatureletSupporter.
        """
        name, featurelet=self._fetch_featurelet(featurelet)
        if self.storage.has_key(name):
            if 'raise_error' in inspect.getargspec(featurelet.removePackage)[0]: #@@ excuse me?!
                featurelet.removePackage(self.context, raise_error=raise_error)
            else:
                featurelet.removePackage(self.context)
            self.storage.pop(name)
## XXX --end complaint

