from opencore.nui.opencoreview import OpencoreView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName
from zope import event
from opencore.interfaces.event import AfterProjectAddedEvent #, AfterSubProjectAddedEvent

class ProjectView(OpencoreView):
    project_preferences = ZopeTwoPageTemplateFile('project-preferences.pt')
    project_create = ZopeTwoPageTemplateFile('project-create.pt')

    def renderUpdateForm(self):
        return self.project_preferences()

    def renderCreateForm(self):
        return self.project_create()

    def createProject(self):
        import pdb; pdb.set_trace()
        putils = getToolByName(self.context, 'plone_utils')
        self.request.set('__initialize_project__', True)
        self.errors = {}
        self.context.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if self.errors:
            self.portal_status_message = ['Please correct the indicated errors.']
            return self.renderCreateForm()

        self.context.processForm(values=self.request)
        projid = self.request.form.get('id')
        projid = putils.normalizeString(projid)
        projects.invokeFactory('OpenProject', projid)
        proj = self.portal.projects._getOb(projid)
        event.notify(AfterProjectAddedEvent(self.context, self.request))
        self.request.response.redirect(proj.absolute_url())

    def updateProject(self):
        pass
