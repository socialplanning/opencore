from zope.interface import implements
from zope.component import adapts

from zope.app.annotation.interfaces import IAnnotations
from BTrees.OOBTree import OOBTree

from opencore.interfaces import IProject
from opencore.nui.project.interfaces import IHomePage

class HomePage(object):
    """store the full url to the project home page
       in an annotation on a project"""

    adapts(IProject)
    implements(IHomePage)

    def __init__(self, context):
        self.context = context
        annot = IAnnotations(context)
        homepage_annot = annot.get('opencore.nui.project.home_page', None)
        if homepage_annot is None:
            homepage_annot = OOBTree()
            annot['opencore.nui.project.home_page'] = homepage_annot
        self.annot = homepage_annot

    def _get_home_page(self):
        project = self.context
        default_page = '%s/%s' % (project.absolute_url(),
                                  project.getDefaultPage())
        return self.annot.get('home_page', default_page)

    def _set_home_page(self, value):
        self.annot['home_page'] = value

    home_page = property(fget=_get_home_page, fset=_set_home_page)
