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

    @formhandler.button('update')
    def handle_request(self):
        # First do validation. We don't treat validation problems as
        # exceptions, because we want to warn user of as many problems
        # as possible, not just the first one that fails.  But this
        # also means this method needs to manually bail out after
        # validation failure, to avoid saving bad data.
        title = self.request.form.get('project_title', self.request.form.get('title'))
        title = text.strip_extra_whitespace(title)
        self.request.form['project_title'] = title
        if not self.valid_title(title):
            self.errors['project_title'] = _(u'err_project_name', u'The name must contain at least 2 characters with at least 1 letter or number.')

        # We're inventing a convention by which viewlets can extend
        # forms with more form data to validate: just provide a
        # validate() method.  (And then later we'll call a save()
        # method.)
        # XXX I'd prefer to just implicitly use viewlet.update(), and
        # not explicitly iterate over them at all; but this view's
        # need to validate *everything* first prevents me from doing
        # that. Maybe this view should be re-architected.
        viewlet_mgr = getMultiAdapter((self.context, self.request, self),
                                      name='opencore.proj_prefs')
        if not hasattr(viewlet_mgr, 'viewlets'):
            # This means it hasn't had update() called yet. only do that once.
            viewlet_mgr.update()
        for viewlet in viewlet_mgr.viewlets:
            if hasattr(viewlet, 'validate'):
                self.errors.update(viewlet.validate())

        if self.errors:
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return

        # Validation passed, so we save the data and set status PSMs.
        allowed_params = set(['__initialize_project__', 'update', 'set_flets',
                              'project_title', 'description', 'logo', 'workflow_policy',
                              'featurelets', 'home-page',
                              'location',])
        new_form = {}
        for k in allowed_params:
            if k in self.request.form:
                if 'project_title' == k:
                    # Aarrgghh!! #*!&% plone snoops into the request, and reads the form variables directly,
                    # so we have to set the form variables with the same names as the schema
                    new_form['title'] = self.request.form[k]
                else:
                    new_form[k] = self.request.form[k]

        reader = IReadWorkflowPolicySupport(self.context)
        old_workflow_policy = reader.getCurrentPolicyId()

        logo = self.request.form.get('logo')
        logochanged = False
        if logo:
            try:
                self.set_logo(logo)
                logochanged = True
            except ValueError:
                pass
            del self.request.form['logo']

        # We're inventing a convention by which viewlets can extend
        # forms with more form data to save: just provide a save
        # method.
        for viewlet in viewlet_mgr.viewlets:
            if hasattr(viewlet, 'save'):
                viewlet.save()
        
        #store change status of flet, security, title, description, logo...
        changed = {
            _(u'psm_project_title_changed') : self.context.title != self.request.form.get('project_title', self.context.title),
            _(u'psm_project_desc_changed') : self.context.Description() != self.request.form.get('description', self.context.Description()),
            _(u'psm_project_logo_changed') : logochanged,
            _(u'psm_security_changed') : old_workflow_policy != self.request.form.get('workflow_policy'),
            #_(u'psm_location_changed'): bool(locationchanged),
            }
        
        supporter = IFeatureletSupporter(self.context)
        flets = [f for n, f in getAdapters((supporter,), IFeaturelet)]

        old_featurelets = set([(f.id, f.title) for f in flets if f.installed])
            
        self.request.form = new_form
        self.context.processForm(REQUEST=self.request, metadata=1)
        featurelets = set([(f.id, f.title) for f in flets if f.installed])

        for flet in featurelets:
            if flet not in old_featurelets:
                changed[_(u'psm_featurelet_added', u'${flet} feature has been added.',
                          mapping={u'flet':flet[1].capitalize()})] = 1
        
        for flet in old_featurelets:
            if flet not in featurelets:
                changed[_(u'psm_featurelet_removed', u'${flet} feature has been removed.',
                          mapping={u'flet':flet[1].capitalize()})] = 1

        
        for field, changed in changed.items():
            if changed:
                self.add_status_message(field)
        #self.add_status_message('Your changes have been saved.')

        home_page = self.request.form.get('home-page', None)
        hpcontext = IHomePage(self.context)
        if home_page is not None:
            if hpcontext.home_page != home_page:
                hp_url = '%s/%s' % (self.context.absolute_url(), home_page)
                self.add_status_message(_(u'psm_proj_homepage_change', u'${project_noun} home page set to: <a href="${hp_url}">${homepage}</a>',
                                        mapping={u'homepage':home_page, u'hp_url':hp_url,
                                                 u'project_noun':self.project_noun.title(),
                                                 }))
                hpcontext.home_page = home_page


        self.redirect(self.context.absolute_url())

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
