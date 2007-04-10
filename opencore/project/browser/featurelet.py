from Products.Five.browser import BrowserView
from topp.featurelets.interfaces import IFeatureletRegistry
from topp.featurelets.interfaces import IFeatureletSupporter
from topp.featurelets.supporter import FeatureletSupporter
from topp.featurelets.interfaces import IMenuSupporter
from topp.featurelets.base import BaseFeaturelet
from zope.component import getUtility
from zope.interface import implements


class FeatureletSupporterView(BrowserView, FeatureletSupporter):
    """
    A view that serves as a featurelet support adapter.  This is
    implemented as a view rather than an adapter because it needs to
    be accessible via traversal in a template for AT edit forms.
    """
    
    implements(IFeatureletSupporter)

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        FeatureletSupporter.__init__(self, context)

    def getSupportableFeaturelets(self):
        """
        Returns a data structure w/ information about all of the
        featurelets that could be supported by the context of this
        view.
        """
        registry = getUtility(IFeatureletRegistry)
        featurelets = registry.getFeaturelets(supporter=self.context)
        for flet in featurelets:
            yield {'id': flet.id,
                   'title': flet.title,
                   'config_view': flet.config_view,
                   }

menu_id = BaseFeaturelet._menu_id


class FeatureletMenuView(BrowserView):
    def __init__(self, context, request):
        self.context = [context]
        self.request = request

    def menu_items(self):
        supporter = IMenuSupporter(self.context[0])
        items = supporter.getMenuItems(menu_id)
        return [item for item in items.values()]
