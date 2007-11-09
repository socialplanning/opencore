from cStringIO import StringIO
from zope.formlib import form
from Products.Five.formlib import formbase
from Products.Five import BrowserView
from Products.OpenPlans.Extensions.create_test_content import create_test_content
from Products.OpenPlans.Extensions.setup import setup_nui
from interfaces import IAddOpenPlans
from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName

class TestContentCreator(formbase.PageForm):
    label = 'Create Dummy Projects and Members'
    form_fields = form.Fields()

    @form.action('Create')
    def handle_create_action(self, action, data):
        self.status = create_test_content(self.context)


class AddOpenPlansForm(formbase.AddForm):
    form_fields = form.Fields(IAddOpenPlans)
    profiles = ('opencore.configuration:default',)

    @property
    def factory(self):
        return self.context.manage_addProduct['CMFPlone'].addPloneSite

    def createAndAdd(self, data):
        self.status='Creating Site\n'
        self.factory(data['id'],
                     data['title'],
                     extension_ids=self.profiles)

        portal = getattr(self.context, data['id'])
        if data.get('testcontent'):
            self.status = self.status + create_test_content(portal)

        self.request.response.redirect(portal.absolute_url())
