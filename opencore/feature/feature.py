from Products.CMFCore.utils import getToolByName
from zope.app.component.hooks import getSite
from zope.schema.vocabulary import SimpleVocabulary

def projectsVocabulary(self):
    """return back all project ids"""
    site = getSite()
    cat = getToolByName(site, 'portal_catalog')
    pbrains = cat(portal_type='OpenProject',
                  sort_on='id',
                  sort_order='ascending',
                  )
    portal = getToolByName(self.context, 'portal_url').getPortalObject()
    feature_ids = set(portal.features.objectIds())
    #XXX will this scale for all projects?
    return SimpleVocabulary.fromValues(b.getId for b in pbrains if ('projfeature-' + b.getId) not in feature_ids)
