from zope.component.factory import Factory
from feature import ProjectFeature

featuredProjectFactory = Factory(
    ProjectFeature,
    title=u'Create a new project',
    description=u'This factory instantiates new featured projects.')
