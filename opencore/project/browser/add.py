"""
project and subproject adding

# @@ needs tests
"""
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from opencore.browser.base import _
from opencore.browser.formhandler import OctopoLite, action
from opencore.interfaces import IHomePage
from opencore.browser.naming import get_view_names
from opencore.project.browser.base import ProjectBaseView
from topp.utils import text
from zope.component import getAdapters, getMultiAdapter
from zope.interface import implements

import logging

log = logging.getLogger('opencore.project.browser.add')

from opencore.framework.editform import AddView
class ProjectAddView(ProjectBaseView, AddView):

    valid_id = staticmethod(text.valid_id)
    valid_title = staticmethod(text.valid_title)
    
    def reserved_names(self):
        return list(get_view_names(self.context)) + ['people', 'projects', 'unique', 'summary', 'pending']

    def handle_validation(self, target=None, fields=None):
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

    def validate(self, request):
        errors = {}

        title = request.form.get('project_title')
        title = text.strip_extra_whitespace(title)
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')
        request.form['project_title'] = title
        if not self.valid_title(title):
            errors['project_title'] = 'The name must contain 2 or more characters.'

        id_ = request.form.get('projid')
        if not self.valid_id(id_):
            errors['id'] = 'The url must contain 2 or more characters.'
        else:
            putils = getToolByName(self.context, 'plone_utils')
            id_ = putils.normalizeString(id_)
            request.form['projid'] = id_
            if self.context.has_key(id_):
                errors['id'] = 'The requested url is already taken.'
        if id_ in self.reserved_names():
            self.errors['id'] = 'Name reserved'
            self.add_status_message(_(u'psm_project_name_reserved',
                                      u'The name "${project_name}" is reserved. Please try a different name.',
                                      mapping={u'project_name':id_}))
        return errors

    def save(self, request, project):
        if 'add' not in request.form:
            return

        hpcontext = IHomePage(project)
        hpcontext.home_page = 'summary'

    def error_handler(self, errors):
        self.errors = errors
        self.add_status_message(_(u'psm_correct_errors_below',
                                  u'Please correct the errors indicated below.'))

    def create(self, request):
        from opencore.project.factory import ProjectFactory
        project = ProjectFactory.new(request, self.context)
        return project
        
    def redirect(self, request):
        return request.response.redirect(self.context.absolute_url())

        



