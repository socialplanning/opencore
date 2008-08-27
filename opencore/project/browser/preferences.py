"""
Preference view
"""
from DateTime import DateTime
from OFS.interfaces import IObjectWillBeRemovedEvent
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.browser import formhandler
from opencore.browser import tal
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


class ProjectPreferencesView(ProjectBaseView, OctopoLite):

    template = ZopeTwoPageTemplateFile('preferences.pt')

    def mangled_logo_url(self):
        """When a project logo is changed, the logo_url remains the same.
        This method appends a timestamp to logo_url to trick the browser into
        fetching the new image instead of using the cached one which could be --
        out of date (and always will be in the ajaxy case).
        """
        logo = self.context.getLogo()
        if logo:
            timestamp = str(DateTime()).replace(' ', '_')
            return '%s?%s' % (logo.absolute_url(), timestamp)
        return self.defaultProjLogoURL

    @action("uploadAndUpdate")
    def change_logo(self, logo=None, target=None, fields=None):
        if logo is None or isinstance(logo, list):
            logo = self.request.form.get("logo")
            
        try:
            self.set_logo(logo)
        except ValueError: # @@ this hides resizing errors
            return

        self.context.reindexObject('logo')
        return {
            'oc-project-logo' : {
                'html': self.logo_html,
                'action': 'replace',
                'effects': 'highlight'
                }
            }

    def set_logo(self, logo):
        try:
            self.context.setLogo(logo)
        except ValueError: # must have tried to upload an unsupported filetype
            # is this the only kind of ValueError that could be raised?
            self.addPortalStatusMessage('Please choose an image in gif, jpeg, png, or bmp format.')
            raise

    @property
    def logo_html(self):
        macro = self.template.macros['logo']
        return tal.render(macro, tal.make_context(self))

    @action("remove")
    def remove_logo(self, target=None, fields=None):
        proj = self.context
        proj.setLogo("DELETE_IMAGE")  # blame the AT API
        proj.reindexObject('logo')
        return {
                'oc-project-logo' : {
                    'html': self.logo_html,
                    'action': 'replace',
                    'effects': 'highlight'
                    }
                }

    def save(self, request):
        # possibly this filtering should happen on the IEditable object?
        new_form = self.filter_params(request)
        old_form = request.form
        request.form = new_form
        from opencore.framework.editform import IEditable
        IEditable(self.context).save(request)
        request.form = old_form

        # this codeblock is equivalent to an opencore.editform viewlet's .save()
        logo = request.form.get('logo')
        if logo:
            try:
                self.set_logo(logo)
            except ValueError:
                pass
            del self.request.form['logo']

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
        from opencore.framework.editform import edit_form_manager
        plugins = edit_form_manager(self)
        request = self.request

        errors = self.validate(request)
        errors.update(plugins.validate(request))
        if errors:
            return self.error_handler(errors)

        self.save(request)
        plugins.save(request)
        
        
    def current_home_page(self):
        return IHomePage(self.context).home_page

    def featurelets(self):
        supporter = IFeatureletSupporter(self.context)
        all_flets = [flet for name, flet in getAdapters((supporter,), IFeaturelet)]
        installed_flets = [flet.id for flet in all_flets if flet.installed]
        flet_data = [dict(id=f.id,
                          title=f.title,
                          url=f._info['menu_items'][0]['action'],
                          checked=f.id in installed_flets,
                          )
                     for f in all_flets]
        return flet_data

    def homepages(self):
        """possible homepages for the app"""        

        flet_data = self.intrinsic_homepages() + self.featurelets()
        return flet_data


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
