from zope.formlib import form
from Products.Five.formlib import formbase
from Products.Five import BrowserView
from Products.OpenPlans.Extensions.create_test_content import create_test_content

class TestContentCreator(formbase.PageForm):
    label = 'Create Dummy Projects and Members'
    form_fields = form.Fields()

    @form.action('Create')
    def handle_create_action(self, action, data):
        self.status = create_test_content(self.context)
