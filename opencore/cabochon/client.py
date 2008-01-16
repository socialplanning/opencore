from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import getToolByName
from cabochonclient import CabochonClient
from opencore.cabochon.interfaces import ICabochonClient
from opencore.configuration.utils import product_config
from threading import Thread
from zope.component import getUtility
from zope.interface import implements

# cache cabochon thread at module level
cabochon_client = None

class CabochonUtility(SimpleItem):
    """local utility to handle communications with cabochon"""

    implements(ICabochonClient)

    def __init__(self, context):
        """initialize cabochon utility with portal context"""
        self.context = context

        # get cabochon_uri from portal properties
        ptool = getToolByName(context, 'portal_properties')
        ocprops = ptool._getOb('opencore_properties')
        cabochon_uri = ocprops.getProperty('cabochon_uri')
        if cabochon_uri is None:
            raise ValueError('"cabochon_uri" no set in portal_properties')
        self.cabochon_uri = cabochon_uri = cabochon_uri.strip()

        # get cabochon_messages filesystem location from configuration
        self.cabochon_messages_dir = product_config('cabochon_messages',
                                                    'opencore.nui')

    @property
    def client(self):
        """return a reference to the global cached thread"""
        #FIXME does this need to be cached?
        global cabochon_client

        if cabochon_client is None:
            # initialize cabochon client
            cabochon_client = CabochonClient(self.cabochon_messages_dir, self.cabochon_uri)

            # initialize the thread
            sender = cabochon_client.sender()

            # and start it
            thread = Thread(target=sender.send_forever)
            thread.setDaemon(True)
            thread.start()

        return cabochon_client

    def notify_project_deleted(self, id):
        event_name = 'project-deleted'
        uri = '%s/events/fire_by_name/%s' % (self.cabochon_uri, event_name)
        self.client.send_message(dict(id=id), uri)
