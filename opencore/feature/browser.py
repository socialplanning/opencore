from Products.Five.formlib import formbase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from opencore.browser.base import BaseView
from zope.formlib import form
from zope.component import createObject
from zope import schema

class FeatureAddView(formbase.Form, BaseView):
    """add a new featured project"""

    template = ViewPageTemplateFile('feature_form.pt')

    prefix = ''
    label = u'Add a featured project'

    form_fields = form.FormFields(
        schema.TextLine(title=u'Title',
                        description=u'Feature Title',
                        __name__='title',
                        required=True),
        schema.Text(title=u'Description',
                    description=u'Feature Description',
                    __name__='description',
                    required=True),
        schema.Choice(title=u'Featured project',
                      description=u'Featured project',
                      __name__='proj_id',
                      vocabulary='opencore.projects',
                      required=True),
        )

    @form.action(u'Add', prefix='')
    def handle_add(self, action, data):
        proj_id = data['proj_id']
        project_feature = createObject('opencore.feature.project',
                                       self.context,
                                       data['proj_id'],
                                       data['title'],
                                       data['description'],
                                       data['proj_id'],
                                       )
        self.request.response.redirect(project_feature.absolute_url())

class FeatureEditView(formbase.EditForm, BaseView):
    """Edit a featured project"""

    template = ViewPageTemplateFile('feature_form.pt')

    prefix = ''
    label = u'Edit a featured project'

    form_fields = form.FormFields(
        schema.TextLine(title=u'Title',
                        description=u'Feature Title',
                        __name__='title',
                        required=True),
        schema.Text(title=u'Description',
                    description=u'Feature Description',
                    __name__='description',
                    required=True),
        )

    @form.action('Save changes', prefix='')
    def handle_save(self, action, data):
        self.context.setTitle(data['title'])
        self.context.setDescription(data['description'])
        self.context.reindexObject()
        self.request.response.redirect(self.context.absolute_url())
