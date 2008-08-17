from Products.OpenPlans.content.project import *

from zope.interface import implements
from zope.component import adapts

from opencore.browser.editform import IEditable
from opencore.interfaces import IProject

from topp.utils import text

class ProjectEditAdapter(object):
    implements(IEditable)
    adapts(IProject)

    def __init__(self, context):
        self.context = context

    def validate(self, request):
        errors = {}
        title = request.form.get('project_title', request.form.get('title'))
        title = text.strip_extra_whitespace(title)
        request.form['project_title'] = title
        if not text.valid_title(title):
            errors['project_title'] = _(u'err_project_name',
                                        u'The name must contain at least 2 characters with at least 1 letter or number.')

        return errors

    def save(self, request):
        self.context.processForm(REQUEST=request, metadata=1)
