import os
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

        # get the cabochon username and password
        cabochon_user_info_file = product_config('cabochon_user_info',
                                                 'opencore.nui')
        
        if not cabochon_user_info_file:
            raise ValueError('no cabochon_user_info file specified in zope.conf opencore.nui')

        try:
            f = open(cabochon_user_info_file)
            self.username, self.password = f.read().strip().split(':', 1)
            f.close()
        except IOError:
            raise ValueError('bad cabochon_user_info file specified in zope.conf opencore.nui')

        # get cabochon_messages filesystem location from configuration
        self.cabochon_messages_dir = product_config('cabochon_messages',
                                                    'opencore.nui')

        if not self.cabochon_messages_dir:
            raise ValueError('no cabochon_messages directory specified in zope.conf opencore.nui')

        if not os.path.exists(self.cabochon_messages_dir):
            raise ValueError('bad cabochon_messages directory specified in zope.conf opencore.nui')

    @property
    def client(self):
        """return a reference to the global cached thread"""
        #FIXME does this need to be cached?
        global cabochon_client

        if cabochon_client is None:

            # get cabochon_uri from portal properties
            # this has to happen here, because we need to have the cabochon_uri set
            # which can't happen unless we already have a portal
            # so we won't have it when we instantiate the cabochon client utility
            ptool = getToolByName(self.context, 'portal_properties')
            ocprops = ptool._getOb('opencore_properties')
            cabochon_uri = ocprops.getProperty('cabochon_uri')
            if cabochon_uri is None:
                raise ValueError('"cabochon_uri" not set in portal_properties')
            self.cabochon_uri = cabochon_uri.strip()

            # initialize cabochon client
            cabochon_client = CabochonClient(self.cabochon_messages_dir,
                                             self.cabochon_uri,
                                             self.username,
                                             self.password)

            # initialize the thread
            sender = cabochon_client.sender()

            # and start it
            thread = Thread(target=sender.send_forever)
            thread.setDaemon(True)
            thread.start()

        return cabochon_client

    def notify_project_deleted(self, id):
        event_name = 'delete_project'
        uri = '%s/event/fire_by_name/%s' % (self.cabochon_uri, event_name)
        self.client.send_message(dict(id=id), uri)
