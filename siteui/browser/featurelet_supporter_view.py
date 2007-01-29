from zope.interface import implements
from zope.component import getUtility

from Products.Five.browser import BrowserView
from topp.featurelets.interfaces import IFeatureletSupporter
from topp.featurelets.interfaces import IFeatureletRegistry
from topp.featurelets.supporter import FeatureletSupporter

def saveFeaturelets(obj, event):
    """
    IObjectModified event subscriber that installs the appropriate
    featurelets.
    """
    req = obj.REQUEST
    if req.get('set_flets') is None:
        # don't do anything unless we're actually coming from the
        # project edit screen
        return

    # XXX there must be a better way... :-|
    if req.get('flet_recurse_flag') is not None:
        return
    req.set('flet_recurse_flag', True)
    registry = getUtility(IFeatureletRegistry)
    supporter = IFeatureletSupporter(obj)

    desired = req.get('featurelets')
    if desired is None:
        desired = tuple()
    desired = set(desired)
    installed = set(supporter.getInstalledFeatureletIds())

    needed = desired.difference(installed)
    for flet_id in needed:
        flet = registry.getFeaturelet(flet_id)
        supporter.installFeaturelet(flet)

    removed = installed.difference(desired)
    for flet_id in removed:
        flet = registry.getFeaturelet(flet_id)
        supporter.removeFeaturelet(flet)


class FeatureletSupporterView(BrowserView, FeatureletSupporter):
    """
    A view that serves as a featurelet support adapter.  This is
    implemented as a view rather than an adapter because it needs to
    be accessible via traversal in a template for AT edit forms.
    """

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

    implements(IFeatureletSupporter)
