from memojito import memoizedproperty

from opencore.featurelets.satellite import SatelliteFeaturelet
from opencore.wordpress.interfaces import \
    IWordpressFeatureletInstalled, IWordpressContainer

class WordPressFeaturelet(SatelliteFeaturelet):
    """
    A featurelet that installs a WordPress blog
    """

    id = "blog"
    title = "WordPress"
    installed_marker = IWordpressFeatureletInstalled

    _info = {'menu_items': ({'title': u'blog',
                             'description': u'WordPress',
                             'action': 'blog'
                             },
                            ),
             }
