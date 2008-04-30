"""
project and subproject adding

# @@ needs tests
"""
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.browser.base import _
from opencore.browser.formhandler import OctopoLite, action
from opencore.geotagging.view import get_geo_writer
from opencore.interfaces import IHomePage
from opencore.interfaces.event import AfterProjectAddedEvent
from opencore.nui.wiki.add import get_view_names
from opencore.project.browser.base import ProjectBaseView
from topp.featurelets.interfaces import IFeatureletSupporter, IFeaturelet
from topp.utils import text
from zope import event
from zope.component import getAdapters
from zope.interface import implements
import logging

log = logging.getLogger('opencore.project.browser.add')

from opencore.browser.base import BaseView
from opencore.interfaces.workflow import IWriteWorkflowPolicySupport
from Products.Five.formlib.formbase import Form
from zope import schema
from zope.app.form import CustomWidgetFactory
from zope.app.form.browser import RadioWidget
from zope.formlib import form
from zope.component import createObject
from zope.component.factory import Factory
from zope.schema.vocabulary import SimpleVocabulary

class ProjectFactory(Factory):
    def __init__(self):
        super(Factory, self).__init__(self)

    def __call__(self, context, id, title, description, security):
        context.invokeFactory('OpenProject', id)
        project = context._getOb(id)

        # set the project's basic stuff
        project.setTitle(title)
        project.setDescription(description)

        #create the project's team
        project._createTeam()

        #set the workflow policy
        IWriteWorkflowPolicySupport(project).setPolicy(security)

        #create the default project index page
        project._createIndexPage()

        #remove the owner role to prevent assigning special permission
        #to creator of project ... should just be project admin
        owners = project.users_with_local_role("Owner")
        project.manage_delLocalRoles(owners)

        hpcontext = IHomePage(project)
        hpcontext.home_page = 'summary'

        #XXX is this reindex needed?
        project.reindexObject()

        return project


def project_security_vocabulary(context):
    return SimpleVocabulary.fromItems([
        (u'Anyone can view this group and any Livable Streets member can contribute to it', 'open_policy'),
        (u'Anyone can view this group but only team members can contribute to it', 'medium_policy'),
        (u'Only team members can view, contribute, or search for this group', 'closed_policy')])

class FormlibProjectAddView(Form, BaseView):
    """make this viewable ttw"""

    #XXX projtxt this
    label = u'Add a project'

    prefix = u''

    #XXX we can make custom javascript widgets for some of these
    #XXX we will leave out the logo for now
    form_fields = form.FormFields(
        schema.TextLine(title=u'Name', __name__='name', required=True),
        schema.TextLine(title=u'URL', __name__='url', required=True),
        schema.Text(title=u'Description', __name__='description', required=False),
        schema.Choice(title=u'Security', __name__='security', required=True,
                      vocabulary='Project security',
                      default='medium_policy'))

    form_fields['security'].custom_widget = CustomWidgetFactory(RadioWidget)

    @form.action(u'Add', prefix=u'')
    def handle_add(self, action, data):
        title = data['name']
        url = data['url']
        description = data.get('description', u'')
        #XXX will need to go through vocabulary here
        security = data['security']
        #XXX and the vocabulary will obviate this
        security = security.encode('utf-8')

        #delegate creation of object to factory
        project = createObject('opencore.project', self.context, url, title, description, security)

        self.redirect(project.absolute_url())


class ProjectAddView(ProjectBaseView, OctopoLite):

    template = ZopeTwoPageTemplateFile('create.pt')
    valid_id = staticmethod(text.valid_id)
    valid_title = staticmethod(text.valid_title)
    
    def reserved_names(self):
        return list(get_view_names(self.context)) + ['people', 'projects', 'unique', 'summary']

    @action('validate')
    def validate(self, target=None, fields=None):
        putils = getToolByName(self.context, 'plone_utils')
        errors = {}
        id_ = self.request.form.get('projid')
        id_ = putils.normalizeString(id_)
        if (self.context.has_key(id_)
            or id_ in self.reserved_names()):
            errors['oc-id-error'] = {
                'html': 'The requested url is already taken.',
                'action': 'copy',
                'effects': 'highlight'
                }
        else:
            errors['oc-id-error'] = {
                'html': '',
                'action': 'copy',
                'effects': ''
                }
        return errors

    def check_logo(self, project, logo):
        try:
            project.setLogo(logo)
        except ValueError: # must have tried to upload an unsupported filetype
            self.addPortalStatusMessage('Please choose an image in gif, jpeg, png, or bmp format.')
            return False
        return True

    @action('add')
    def handle_request(self, target=None, fields=None):
        #XXX all of the errors that are reported back here are not going
        # through the translation machinery
        putils = getToolByName(self.context, 'plone_utils')
        self.request.set('__initialize_project__', True)

        self.errors = {}
        title = self.request.form.get('project_title')
        title = text.strip_extra_whitespace(title)
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')
        self.request.form['project_title'] = title
        if not self.valid_title(title):
            self.errors['project_title'] = 'The name must contain ' \
              'at least 2 characters with at least 1 letter or number.'

        id_ = self.request.form.get('projid')
        if not self.valid_id(id_):
            self.errors['id'] = 'The url may contain only letters, numbers, hyphens, or underscores and must have at least 1 letter or number.'
        else:
            id_ = putils.normalizeString(id_)
            if self.context.has_key(id_):
                self.errors['id'] = 'The requested url is already taken.'

        geowriter = get_geo_writer(self)
        geo_info, locationchanged = geowriter.get_geo_info_from_form(
            old_info={})
        self.errors.update(geo_info.get('errors', {}))

        if self.errors:
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return

        self.request.form['featurelets'] = [f['id'] for f in self.featurelets()]

        # Aarrgghh!! #*!&% plone snoops into the request, and reads the form variables directly,
        # so we have to set the form variables with the same names as the schema
        self.request.form['title'] = title

        proj = self.context.restrictedTraverse('portal_factory/OpenProject/%s' %id_)
        # not calling validate because it explodes on "'" for project titles
        # XXX is no validation better than an occasional ugly error?
        #proj.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if self.errors:
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return 
        if id_ in self.reserved_names():
            self.errors['id'] = 'Name reserved'
            self.add_status_message(_(u'psm_project_name_reserved', u'The name "${project_name}" is reserved. Please try a different name.',
                                      mapping={u'project_name':id_}))
            return

        self.context.portal_factory.doCreate(proj, id_)
        proj = self.context._getOb(id_)
        self.notify(proj)

        logo = self.request.form.get('logo')
        if logo:
            if not self.check_logo(proj, logo):
                return
            del self.request.form['logo']

        get_geo_writer(self, proj).save_coords_from_form()

        hpcontext = IHomePage(proj)
        hpcontext.home_page = 'summary'

        self.template = None
        site_url = getToolByName(self.context, 'portal_url')()
        proj_edit_url = '%s/projects/%s/project-home/edit' % (site_url, id_)

        s_message_mapping = {'title': title, 'proj_edit_url': proj_edit_url,
                             'project_noun': self.project_noun,}


        s_message = _(u'project_created',
                      u'"${title}" has been created. Create a team by searching for other members to invite to your ${project_noun}, then <a href="${proj_edit_url}">edit your ${project_noun} home page</a>.',
                      mapping=s_message_mapping)
        
#        self.add_status_message(s_message)

        self.redirect('%s/tour' % proj.absolute_url())

    def notify(self, project):
        event.notify(AfterProjectAddedEvent(project, self.request))

    def featurelets(self):
        # create a stub object that provides IFeatureletSupporter
        # is there a better way to get the list of adapters without having
        # the "for" object?

        # @@ dwm: look at the adapter reg or uses the apidoc api which
        # featurelet to display is a policy decision on the portal
        # (like opencore_properties). Might work best to build the ui
        # around a policy abstraction
        
        obj = DummyFeatureletSupporter()
        flets = getAdapters((obj,), IFeaturelet)
        flet_data = [dict(id=f.id,
                          title=f.title,
                          url=f._info['menu_items'][0]['action'],
                          checked=False,
                          )
                     for name, f in flets]
        return flet_data

    def homepages(self):
        flet_data = self.intrinsic_homepages() + self.featurelets()
        return flet_data


class DummyFeatureletSupporter(object):
    implements(IFeatureletSupporter)

