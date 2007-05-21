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

    def handleCreate(self):
        putils = getToolByName(self.context, 'plone_utils')
        self.request.set('__initialize_project__', True)

        self.errors = {}
        self.context.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if self.errors:
            self.portal_status_message = ['Please correct the indicated errors.']
            return self.renderCreateForm()
        # TODO this is not enforcing non-empty project full names

        projid = self.request.form.get('projid')
        projid = putils.normalizeString(projid)
        self.portal.projects.projects.invokeFactory('OpenProject', projid)
        proj = self.portal.projects._getOb(projid)

        event.notify(AfterProjectAddedEvent(proj, self.request))
        self.request.response.redirect(proj.absolute_url())

    def handleUpdate(self):
        pass
