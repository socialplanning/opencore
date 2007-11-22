from BTrees.OOBTree import OOBTree
from opencore.interfaces import IHomePage
from opencore.interfaces import IProject
from zope.app.annotation.interfaces import IAnnotations
from zope.component import adapts
from zope.interface import implements
import re


class HomePage(object):
    """store the full url to the project home page
       in an annotation on a project"""

    adapts(IProject)
    implements(IHomePage)

    _allowed_home_page_re = re.compile("^[\w/:\.-]*$")

    def __init__(self, context):
        self.context = context
        annot = IAnnotations(context)
        homepage_annot = annot.get('opencore.project.browser.home_page', None)
        if homepage_annot is None:
            homepage_annot = OOBTree()
            annot['opencore.project.browser.home_page'] = homepage_annot
        self.annot = homepage_annot

    def _get_home_page(self):
        return self.annot.get('home_page', 'project-home')

    def _set_home_page(self, value):
        assert self._allowed_home_page_re.match(value)
        self.annot['home_page'] = value

    home_page = property(fget=_get_home_page, fset=_set_home_page)
