from Products.CMFCore.utils import getToolByName
from Products.Five.formlib import formbase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from opencore.browser.base import BaseView
from zope.formlib import form
from zope.component import createObject
from zope import schema

projfeature_prefix = 'projfeature-'

class FeatureAddView(formbase.Form, BaseView):
    """add a new featured project"""

    template = ViewPageTemplateFile('feature_add_form.pt')

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
        schema.Text(title=u'Text',
                    description=u'Feature Text',
                    __name__='text',
                    required=True),
        schema.Choice(title=u'Featured project',
                      description=u'Featured project',
                      __name__='proj_id',
                      vocabulary='opencore.projects',
                      required=True),
        )

    def project_from_request(self):
        try:
            proj_id = self.request.form['project']
            portal = getToolByName(self.context, 'portal_url')
            return portal.projects._getOb(proj_id)
        except KeyError:
            pass

    @form.action(u'Add', prefix='')
    def handle_add(self, action, data):
        proj_id = data['proj_id']
        project_feature = createObject('opencore.feature.project',
                                       self.context,
                                       projfeature_prefix + data['proj_id'],
                                       data['title'],
                                       data['description'],
                                       data['text'],
                                       data['proj_id'],
                                       )
        self.request.response.redirect(project_feature.absolute_url())

class FeatureEditView(formbase.Form, BaseView):
    """Edit a featured project"""

    template = ViewPageTemplateFile('feature_edit_form.pt')

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
        schema.Text(title=u'Text',
                    description=u'Feature Text',
                    __name__='text',
                    required=True),
        schema.Choice(title=u'Featured project',
                      description=u'Featured project',
                      __name__='proj_id',
                      vocabulary='opencore.projects',
                      required=True),
        )

    @form.action('Save changes', prefix='')
    def handle_save(self, action, data):
        cur_proj_id = self.context.getId()[len(projfeature_prefix):]
        new_proj_id = data['proj_id']
        if cur_proj_id != new_proj_id:
            #we need to rename the object
            #XXX this will give us copy errors if we try to set the id to something that already exists
            parent = self.context.aq_inner.aq_parent
            parent.manage_renameObject(projfeature_prefix + cur_proj_id, projfeature_prefix + new_proj_id)
            self.context = parent._getOb(projfeature_prefix + new_proj_id)
            # and we need to also update the reference
            self.context.deleteReferences(relationship='opencore.featured.project')
            portal = getToolByName(self.context, 'portal_url').getPortalObject()
            proj = portal.projects._getOb(new_proj_id)
            self.context.addReference(proj, relationship='opencore.featured.project')

        self.context.setTitle(data['title'])
        self.context.setDescription(data['description'])
        self.context.setText(data['text'])
        self.context.reindexObject()
        self.request.response.redirect(self.context.absolute_url())
