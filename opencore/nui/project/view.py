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

        id = self.request.get('projid')
        if not id:
            self.errors = {'projid' : 'You need to enter a short name for the project'}
            self.portal_status_message = ['Please correct the indicated errors.', "%s" % self.errors]
            return self.renderCreateForm()
        
        stub = self.context.restrictedTraverse('portal_factory/OpenProject/' + id)
        
        transaction_note('Initiated creation of %s with id %s in %s' % (stub.getTypeInfo().getId(), id, context.absolute_url()))
        
        
        self.errors = {}
        stub.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if not self.request.get('full_name'):
            self.errors['full_name'] = 'Please add a full name'
        if self.errors:
            self.portal_status_message = ['Please correct the indicated errors.', "%s" % self.errors]
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
