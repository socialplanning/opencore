from Products.Five import BrowserView

from topp.featurelets.interfaces import IMenuSupporter
from topp.featurelets.base import BaseFeaturelet

menu_id = BaseFeaturelet._menu_id

class FeatureletMenuView(BrowserView):
    def __init__(self, context, request):
        self.context = [context]
        self.request = request

    def menu_items(self):
        supporter = IMenuSupporter(self.context[0])
        items = supporter.getMenuItems(menu_id)
        return [item for item in items.values()]
