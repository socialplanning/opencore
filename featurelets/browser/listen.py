from Products.Five import BrowserView

from Products.listen.content.mailinglist import MailingList

from topp.featurelets.interfaces import IFeatureletSupporter

from opencore.featurelets.listen import ListenFeaturelet

class ListenConfigView(BrowserView):
    """
    View object that renders the configuration page for the listen
    featurelet.
    """
    def __init__(self, context, request):
        self._context = (context,)
        self.request = request

    @property
    def context(self):
        return self._context[0]

    @property
    def lists(self):
        supporter = IFeatureletSupporter(self.context)
        descriptor = supporter.getFeatureletDescriptor(ListenFeaturelet.id)
        container = self.context._getOb(descriptor['content'][0]['id'])
        lists = container.objectValues(spec=MailingList.meta_type)
        return lists
