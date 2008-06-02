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
                                       data['title'],
                                       data['description'],
                                       proj_id,
                                       )
        #XXX this doesn't work because we didn't set up the fti
        #(it sets it correctly, but getLayout asks the fti, which isn't set)
        project_feature.setLayout('view')

        self.context[proj_id] = project_feature

        #XXX this also doesn't work because something isn't set right
        # getPhysicalPath on the project_feature object is empty
        #self.request.response.redirect(project_feature.absolute_url())

        #XXX we redirect to /view because the default view on features
        #isn't set up right
        self.request.response.redirect(
            '%s/%s/view' % (self.context.absolute_url(), proj_id))

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
        self.context.title = data['title']
        self.context.description = data['description']
        #XXX this is what it can be when we work out the urls
        #self.request.response.redirect(self.context.absolute_url())
        self.request.response.redirect(
            self.request.ACTUAL_URL.replace('edit', 'view'))
