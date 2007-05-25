from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import transaction_note
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.interfaces.event import AfterProjectAddedEvent #, AfterSubProjectAddedEvent
from opencore.nui.base import BaseView, button
from zExceptions import BadRequest
from zExceptions import Redirect
from zope import event


class ProjectPreferencesView(BaseView):

    @button('update')
    def handle_request(self):
        self.context.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)        
        self.context.processForm(REQUEST=self.request)
        self.redirect(self.context.absolute_url())


class ProjectAddView(BaseView):

    @button('add')
    def handle_request(self):
        putils = getToolByName(self.context, 'plone_utils')
        self.request.set('__initialize_project__', True)

        self.errors = {}
        if not self.request.get('full_name'):
            self.errors['full_name'] = 'Please add a full name'

        title = self.request.form.get('title')
        if not title:
            self.errors['title'] = 'You need to enter a short name for the project'
        id_ = putils.normalizeString(title)
        if self.context.has_key(id_):
            self.errors = {'title' : 'The requested short name is already taken.'}
            self.portal_status_message = ['Please correct the indicated errors.']          

        if self.errors:
            self.portal_status_message = ['Please correct the indicated errors.']
            return 

        proj = self.context.restrictedTraverse('portal_factory/OpenProject/%s' %id_)
        proj.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if self.errors:
            transaction_note('Started creation of project: %s' %title)
            self.portal_status_message = ['Please correct the indicated errors.']
            return 

        self.context.portal_factory.doCreate(proj, id_)
        proj = self.context._getOb(id_)
        event.notify(AfterProjectAddedEvent(proj, self.request))
        transaction_note('Finished creation of project: %s' %title)
        self.request.RESPONSE.redirect(proj.absolute_url())



