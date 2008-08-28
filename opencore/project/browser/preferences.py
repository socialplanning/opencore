"""
Preference view
"""
from OFS.interfaces import IObjectWillBeRemovedEvent
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.browser import formhandler
from opencore.browser.base import _
from opencore.browser.formhandler import OctopoLite, action
from opencore.interfaces import IHomePage
from opencore.interfaces import IProject
from opencore.interfaces.adding import IAddProject
from opencore.interfaces.workflow import IReadWorkflowPolicySupport
from opencore.project.browser.base import ProjectBaseView
from opencore.interfaces.membership import IEmailInvites
from topp.featurelets.interfaces import IFeatureletSupporter
from topp.featurelets.supporter import FeatureletSupporter, IFeaturelet
from topp.utils import text
from topp.utils import zutils
from zope.app.container.contained import IObjectRemovedEvent
from zope.component import adapter, adapts
from zope.interface import implements
from zope.component import getUtility, getAdapters, getMultiAdapter

import inspect
import logging

log = logging.getLogger('opencore.project.browser.preferences')

from opencore.framework.editform import EditView
class ProjectPreferencesView(ProjectBaseView, OctopoLite, EditView):

    template = ZopeTwoPageTemplateFile('preferences.pt')

    def save(self, request):
        # possibly this filtering should happen on the IEditable object?
        new_form = self.filter_params(request)
        old_form = request.form
        request.form = new_form
        from opencore.framework.editform import IEditable
        IEditable(self.context).save(request)
        request.form = old_form

        # this codeblock is equivalent to an opencore.editform viewlet's .save()
        home_page = request.form.get('home-page', None)
        hpcontext = IHomePage(self.context)
        if home_page is not None:
            if hpcontext.home_page != home_page:
                hp_url = '%s/%s' % (self.context.absolute_url(), home_page)
                hpcontext.home_page = home_page


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

    @formhandler.button('update')
    def handle_request(self):
        self.POST()        
        self.template = None
        self.redirect('%s/tour' % self.context.absolute_url())

    def current_home_page(self):
        return IHomePage(self.context).home_page

    def homepages(self):
        """possible homepages for the app"""        

        from opencore.project.browser.home_page import IHomePageable
        from zope.component import subscribers
        homepages = subscribers((self.context,), IHomePageable)
        
        homepage_data = []
        for homepage in homepages:
            checked = homepage.url == self.current_home_page()
            homepage_data.append(dict(id=homepage.id,
                                  title=homepage.title,
                                  url=homepage.url,
                                  checked=checked))
        return homepage_data


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

@adapter(IProject, IObjectRemovedEvent)
def delete_email_invites(proj, event=None):
    invite_util = getUtility(IEmailInvites, context=proj)
    invite_util.removeAllInvitesForProject(proj.getId())

@adapter(IProject, IObjectWillBeRemovedEvent)
def handle_blog_delete(project, event=None):
    pass

## XXX --end complaint

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
