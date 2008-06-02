from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.DynamicType import DynamicType
from Products.CMFCore.utils import getToolByName
from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin
from interfaces import IProjectFeature
from zope.app.component.hooks import getSite
from zope.interface import implements
from zope.schema.vocabulary import SimpleVocabulary

#XXX all these base classes, and things aren't working right
# must be an easier way :)
class ProjectFeature(SimpleItem,
                     DynamicType,
                     CMFCatalogAware,
                     PropertyManager,
                     BrowserDefaultMixin):
    """implementation of a featured item geared towards projects"""

    implements(IProjectFeature)

    def __init__(self, title, description, proj_id):
        self.proj_id = proj_id
        self.title = title
        self.description = description

    @property
    def link(self):
        site = getSite()
        return '%s/projects/%s' % (
            getToolByName(site, 'portal_url')(),
            self.proj_id)

    @property
    def image_url(self):
        return '%s/logo_square_thumb' % self.link

def projectsVocabulary(self):
    """return back all project ids"""
    site = getSite()
    cat = getToolByName(site, 'portal_catalog')
    pbrains = cat(portal_type='OpenProject',
                  sort_on='id',
                  sort_order='ascending',
                  )
    #XXX will this scale for all projects?
    return SimpleVocabulary.fromValues(b.id for b in pbrains)
