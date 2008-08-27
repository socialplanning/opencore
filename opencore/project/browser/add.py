"""
project and subproject adding

# @@ needs tests
"""
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.browser.base import _
from opencore.browser.formhandler import OctopoLite, action
from opencore.interfaces import IHomePage
from opencore.interfaces.event import AfterProjectAddedEvent
from opencore.browser.naming import get_view_names
from opencore.project.browser.base import ProjectBaseView
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
    def handle_validation(self, target=None, fields=None):
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

    def validate(self, request):
        errors = {}

        title = request.form.get('project_title')
        title = text.strip_extra_whitespace(title)
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')
        request.form['project_title'] = title
        if not self.valid_title(title):
            errors['project_title'] = 'The name must contain 2 or more characters.'

        id_ = request.form.get('projid')
        if not self.valid_id(id_):
            errors['id'] = 'The url must contain 2 or more characters.'
        else:
            putils = getToolByName(self.context, 'plone_utils')
            id_ = putils.normalizeString(id_)
            request.form['projid'] = id_
            if self.context.has_key(id_):
                errors['id'] = 'The requested url is already taken.'
        if id_ in self.reserved_names():
            self.errors['id'] = 'Name reserved'
            self.add_status_message(_(u'psm_project_name_reserved',
                                      u'The name "${project_name}" is reserved. Please try a different name.',
                                      mapping={u'project_name':id_}))

    def save(self, request):
        proj = self.context[request.form['projid']]

        logo = request.form.get('logo')
        if logo:
            if not self.check_logo(proj, logo):
                # the above call actually sets the logo. yuck.
                return
            del request.form['logo']

        hpcontext = IHomePage(proj)
        hpcontext.home_page = 'summary'

        # We have to look up the viewlets again, now that we have
        # a project for them to use as the context to save to.
        from opencore.framework.editform import edit_form_manager
        manager = edit_form_manager(self, context=proj)
        manager.save(request)

    def error_handler(self, errors):
        self.errors = errors
        self.add_status_message(_(u'psm_correct_errors_below',
                                  u'Please correct the errors indicated below.'))

    @action('add')
    def handle_request(self, target=None, fields=None):
        #XXX all of the errors that are reported back here are not going
        # through the translation machinery

        from opencore.framework.editform import edit_form_manager
        plugins = edit_form_manager(self)
        request = self.request
        
        request.set('__initialize_project__', True) # @@ what is this for?
        errors = self.validate(request)

        # Give plugin viewlets a chance to validate. We don't have a
        # project yet, so they'll have to tolerate validating with the
        # project container as the context.
        errors.update(plugins.validate(request))
        if errors:
            return self.error_handler(errors)
        
        # Aarrgghh!! #*!&% plone snoops into the request, and reads the form variables directly,
        # so we have to set the form variables with the same names as the schema
        self.request.form['title'] = self.request.form['project_title']
        id_ = self.request.form['projid']

        proj = self.context.restrictedTraverse('portal_factory/OpenProject/%s' %id_)
        # not calling validate because it explodes on "'" for project titles
        # XXX is no validation better than an occasional ugly error?
        #proj.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)

        self.context.portal_factory.doCreate(proj, id_)
        proj = self.context[proj.getId()]
        self.notify(proj)

        self.save(request)  # instead i think it would be much preferable to invoke a save
        # ............ on the newly created project directly:
        # ............ >>> IEditForm(proj).save(request.form) 
        # this is hard, though, because things behave strangely here;
        # the self.notify(proj) [event subscriptions] is where the attributes
        # are actually set on the content...

        self.template = None  # Don't render anything before redirect.
        self.redirect('%s/tour' % proj.absolute_url())

    def notify(self, project):
        event.notify(AfterProjectAddedEvent(project, self.request))



