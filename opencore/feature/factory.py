from Products.CMFCore.utils import getToolByName
from interfaces import IProjectFeature
from zope.component.factory import Factory
from zope.interface import alsoProvides

def create_project_feature(context, id, title, description, text, proj_id):
    # XXX this will generate errors if the project has already been featured
    context.invokeFactory('News Item', id, title=title)
    ni = context._getOb(id)
    alsoProvides(ni, IProjectFeature)
    ni.setTitle(title)
    ni.setDescription(description)
    ni.setText(text)
    portal = getToolByName(context, 'portal_url').getPortalObject()
    proj = portal.projects._getOb(proj_id)
    ni.addReference(proj, relationship='opencore.featured.project')
    ni.setLayout('@@view')
    ni.reindexObject()
    return ni

featuredProjectFactory = Factory(
    create_project_feature,
    title=u'Create a new project',
    description=u'This factory instantiates new featured projects.')
