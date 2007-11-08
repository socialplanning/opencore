from Products.Five import BrowserView

from Products.listen.content.mailinglist import MailingList

from zope.i18nmessageid import MessageFactory

from topp.featurelets.interfaces import IFeatureletSupporter

from opencore.featurelets.listen import ListenFeaturelet

_ = MessageFactory("opencore")

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

class DeleteListView(BrowserView):
    """
    View object that handles the list delete confirmation logic.
    """
    def __init__(self, context, request):
        self._context = (context,)
        self.request = request

    @property
    def context(self):
        return self._context[0]

    def confirmDeleteList(self):
        form = self.request.form
        psm = _(u'psm_mailing_list_deletion_cancelled', u"Mailing list deletion cancelled.")
        list_id = form.get('list_id', '')
        confirm = form.get('%s_confirm_delete' % list_id, 'false')
        if confirm == 'true':
            self.context.manage_delObjects(ids=[list_id])
            psm = _(u'psm_mailing_list_deleted', u"Mailing list deleted.")
        url = "%s?portal_status_message=%s" % (self.context.absolute_url(),
                                               psm)
        self.request.RESPONSE.redirect(url)
