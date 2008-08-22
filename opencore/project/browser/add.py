"""
project and subproject adding

# @@ needs tests
"""
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.browser.base import _
from opencore.browser.formhandler import OctopoLite, action
from opencore.interfaces import IHomePage
from opencore.interfaces.event import AfterProjectAddedEvent
from opencore.nui.wiki.add import get_view_names
from opencore.project.browser.base import ProjectBaseView
from topp.featurelets.interfaces import IFeatureletSupporter, IFeaturelet
from topp.utils import text
from zope import event
from zope.component import getAdapters, getMultiAdapter
from zope.interface import implements

import logging

log = logging.getLogger('opencore.project.browser.add')


class ProjectAddView(ProjectBaseView, OctopoLite):

    template = ZopeTwoPageTemplateFile('create.pt')
    valid_id = staticmethod(text.valid_id)
    valid_title = staticmethod(text.valid_title)
    
    def reserved_names(self):
        return list(get_view_names(self.context)) + ['people', 'projects', 'unique', 'summary', 'pending']

    @action('validate')
    def validate(self, target=None, fields=None):
        putils = getToolByName(self.context, 'plone_utils')
        errors = {}
        id_ = self.request.form.get('projid')
        id_ = putils.normalizeString(id_)
        if (self.context.has_key(id_)
            or id_ in self.reserved_names()):
            errors['oc-id-error'] = {
                'html': 'The requested url is already taken.',
                'action': 'copy',
                'effects': 'highlight'
                }
        else:
            errors['oc-id-error'] = {
                'html': '',
                'action': 'copy',
                'effects': ''
                }
        return errors

    def check_logo(self, project, logo):
        try:
            project.setLogo(logo)
        except ValueError: # must have tried to upload an unsupported filetype
            self.addPortalStatusMessage('Please choose an image in gif, jpeg, png, or bmp format.')
            return False
        return True

    @action('add')
    def handle_request(self, target=None, fields=None):
        #XXX all of the errors that are reported back here are not going
        # through the translation machinery
        putils = getToolByName(self.context, 'plone_utils')
        self.request.set('__initialize_project__', True)

        self.errors = {}
        title = self.request.form.get('project_title')
        title = text.strip_extra_whitespace(title)
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')
        self.request.form['project_title'] = title
        if not self.valid_title(title):
            self.errors['project_title'] = 'The name must contain 2 or more characters.'


        id_ = self.request.form.get('projid')
        if not self.valid_id(id_):
            self.errors['id'] = 'The url must contain 2 or more characters.'
        else:
            id_ = putils.normalizeString(id_)
            if self.context.has_key(id_):
                self.errors['id'] = 'The requested url is already taken.'

        # Give plugin viewlets a chance to validate. We don't have a
        # project yet, so they'll have to tolerate validating with the
        # project container as the context.
        viewlet_mgr = getMultiAdapter((self.context, self.request, self),
                                      name='opencore.proj_prefs')
        if not hasattr(viewlet_mgr, 'viewlets'):
            viewlet_mgr.update()
        viewlets = viewlet_mgr.viewlets
        for viewlet in viewlets:
            if hasattr(viewlet, 'validate'):
                self.errors.update(viewlet.validate())

        # XXX TO DO: handle featurelets, just like in preferences.py

        if self.errors:
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return

        self.request.form['featurelets'] = [f['id'] for f in self.featurelets()]

        # Aarrgghh!! #*!&% plone snoops into the request, and reads the form variables directly,
        # so we have to set the form variables with the same names as the schema
        self.request.form['title'] = title

        proj = self.context.restrictedTraverse('portal_factory/OpenProject/%s' %id_)
        # not calling validate because it explodes on "'" for project titles
        # XXX is no validation better than an occasional ugly error?
        #proj.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)

        location = self.request.form.get('location', u'')
        if location:
            proj.setLocation(location)

        if self.errors:
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return 
        if id_ in self.reserved_names():
            self.errors['id'] = 'Name reserved'
            self.add_status_message(_(u'psm_project_name_reserved', u'The name "${project_name}" is reserved. Please try a different name.',
                                      mapping={u'project_name':id_}))
            return

        self.context.portal_factory.doCreate(proj, id_)
        proj = self.context._getOb(id_)
        self.notify(proj)

        logo = self.request.form.get('logo')
        if logo:
            if not self.check_logo(proj, logo):
                return
            del self.request.form['logo']

        hpcontext = IHomePage(proj)
        hpcontext.home_page = 'summary'

        # We have to look up the viewlets again, now that we have
        # a project for them to use as the context to save to.
        viewlet_mgr = getMultiAdapter((proj, self.request, self),
                                      name='opencore.proj_prefs')
        if not hasattr(viewlet_mgr, 'viewlets'):
            viewlet_mgr.update()
        for viewlet in viewlet_mgr.viewlets:
            if hasattr(viewlet, 'save'):
                viewlet.save()
        
        self.template = None  # Don't render anything before redirect.
        site_url = getToolByName(self.context, 'portal_url')()
        proj_edit_url = '%s/projects/%s/project-home/edit' % (site_url, id_)

        s_message_mapping = {'title': title, 'proj_edit_url': proj_edit_url,
                             'project_noun': self.project_noun,}


        s_message = _(u'project_created',
                      u'"${title}" has been created. Create a team by searching for other members to invite to your ${project_noun}, then <a href="${proj_edit_url}">edit your ${project_noun} home page</a>.',
                      mapping=s_message_mapping)
        
#        self.add_status_message(s_message)

        self.redirect('%s/tour' % proj.absolute_url())

    def notify(self, project):
        event.notify(AfterProjectAddedEvent(project, self.request))

    def featurelets(self):
        # create a stub object that provides IFeatureletSupporter
        # is there a better way to get the list of adapters without having
        # the "for" object?

        # @@ dwm: look at the adapter reg or uses the apidoc api which
        # featurelet to display is a policy decision on the portal
        # (like opencore_properties). Might work best to build the ui
        # around a policy abstraction
        
        obj = DummyFeatureletSupporter()
        flets = getAdapters((obj,), IFeaturelet)
        flet_data = [dict(id=f.id,
                          title=f.title,
                          url=f._info['menu_items'][0]['action'],
                          checked=False,
                          )
                     for name, f in flets]
        return flet_data

    def homepages(self):
        flet_data = self.intrinsic_homepages() + self.featurelets()
        return flet_data


class DummyFeatureletSupporter(object):
    implements(IFeatureletSupporter)

