from zope.interface import implements, Interface
from zope.component import getUtility
from opencore.utility.interfaces import IHTTPClient 
from topp.featurelets.interfaces import IFeaturelet
from topp.featurelets.base import BaseFeaturelet
from Products.CMFCore.utils import getToolByName

from interfaces import IWordpressFeatureletInstalled
from interfaces import IWordpressContainer

from Products.OpenPlans.interfaces import IProject

class WordpressFeaturelet(BaseFeaturelet):
    """
    A featurelet that installs a Wordpress blog
    """

    implements(IFeaturelet)
    
    id = "blog"
    title = "Blog"
    installed_marker = IWordpressFeatureletInstalled

    _info = {'menu_items': ({'title': u'blog',
                             'description': u'Blog',
                             'action': 'blog'
                             },
                            ),
             }

    _required_interfaces = BaseFeaturelet._required_interfaces + (IProject,)

    def deliverPackage(self, obj):
        return BaseFeaturelet.deliverPackage(self, obj)

    def removePackage(self, obj):
        return BaseFeaturelet.removePackage(self, obj)
