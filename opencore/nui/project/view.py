from opencore.nui.opencoreview import OpencoreView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName
from zope import event
from opencore.interfaces.event import AfterProjectAddedEvent #, AfterSubProjectAddedEvent
from zExceptions import BadRequest
from zope.component import getUtility
from topp.featurelets.interfaces import IFeatureletSupporter
from topp.featurelets.interfaces import IFeatureletRegistry

class ProjectView(OpencoreView):
    project_preferences = ZopeTwoPageTemplateFile('project-preferences.pt')
    project_create = ZopeTwoPageTemplateFile('project-create.pt')

    def renderPrefsForm(self):
        return self.project_preferences()

    def renderCreateForm(self):
        return self.project_create()

    def handleCreate(self):
        putils = getToolByName(self.context, 'plone_utils')
        self.request.set('__initialize_project__', True)

        self.errors = {}
        if not self.request.get('full_name'):
            self.errors['full_name'] = 'Please add a full name'

        title = self.request.form.get('title')
        title = putils.normalizeString(title)
        if not title:
            self.errors['title'] = 'You need to enter a short name for the project'

        if self.errors:
            self.portal_status_message = ['Please correct the indicated errors.']
            return self.renderCreateForm()

        try:
            self.portal.projects.projects.invokeFactory('OpenProject', title)
        except BadRequest:
            self.errors = {'title' : 'The requested address is already in use.'}
            self.portal_status_message = ['Please correct the indicated errors.']            
            return self.renderCreateForm()
            
        proj = self.portal.projects._getOb(title)
        proj.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if self.errors:
            self.portal_status_message = ['Please correct the indicated errors.']
            return self.renderCreateForm()


        self.context.portal_factory.doCreate(self.context, title)
        self.handleFeaturelets(proj)
        event.notify(AfterProjectAddedEvent(proj, self.request))
        self.request.response.redirect(proj.absolute_url())

    def handleFeaturelets(self, proj):
        if self.request.get('flet_recurse_flag') is not None:
            return
        self.request.set('flet_recurse_flag', True)
        registry = getUtility(IFeatureletRegistry)
        supporter = IFeatureletSupporter(proj)
        
        desired = self.request.get('featurelets')
        if desired is None:
            desired = tuple()
        desired = set(desired)
        installed = set(supporter.getInstalledFeatureletIds())

        needed = desired.difference(installed)
        for flet_id in needed:
            flet = registry.getFeaturelet(flet_id)
            supporter.installFeaturelet(flet)

        removed = installed.difference(desired)
        for flet_id in removed:
            flet = registry.getFeaturelet(flet_id)
            supporter.removeFeaturelet(flet)


    def handlePrefs(self):
        self.context.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)        
        self.handleFeaturelets(self.context)
        self.context.processForm(REQUEST=self.request)
        self.request.response.redirect(self.context.absolute_url())
