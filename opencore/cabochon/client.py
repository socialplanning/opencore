from OFS.SimpleItem import SimpleItem
from cabochonclient import CabochonClient
from opencore.cabochon.interfaces import ICabochonClient
from opencore.configuration.utils import product_config, get_config
from threading import Thread
from zope.interface import implements

# cache cabochon thread at module level
cabochon_client = None

class CabochonConfigError(Exception):
    """Error in cabochon configuration"""

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
            raise CabochonConfigError('no cabochon_user_info file specified in zope.conf opencore.nui')

        try:
            f = open(cabochon_user_info_file)
            self.username, self.password = f.read().strip().split(':', 1)
            f.close()
        except IOError:
            raise CabochonConfigError('bad cabochon_user_info file specified in zope.conf opencore.nui')

        # get cabochon_messages filesystem location from configuration
        self.cabochon_messages_dir = product_config('cabochon_messages',
                                                    'opencore.nui')

        if not self.cabochon_messages_dir:
            raise CabochonConfigError('no cabochon_messages directory specified in zope.conf opencore.nui')

    @property
    def client(self):
        """return a reference to the global cached thread"""
        #FIXME does this need to be locked?
        global cabochon_client

        if cabochon_client is None:
            # get cabochon_uri from configuration.
            # This used to need to happen here, because we used to
            # read it from portal_properties which can't happen unless
            # we already have a portal so we won't have it when we
            # instantiate the cabochon client utility.

            # XXX Now that we read the config from the filesystem,
            # where should this go? Based on the above comment, I
            # tried moving it to __init__ but then I get an
            # AttributeError: 'NoneType' object has no attribute
            # 'send_message'.
            cabochon_uri = get_config('applications', 'cabochon uri', None)
            if cabochon_uri is None:
                raise CabochonConfigError('"cabochon uri" not set in build.ini')
	    cabochon_uri = cabochon_uri.strip()
	    if not cabochon_uri:
	        raise CabochonConfigError('invalid empty cabochon uri')
            self.cabochon_uri = cabochon_uri

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

    def notify_project_created(self, id, creatorid):
        client = self.client
        event_name = 'create_project'
        uri = '%s/event/fire_by_name/%s' % (self.cabochon_uri, event_name)
        client.send_message(dict(id=id, creator=creatorid), uri)

    def notify_project_deleted(self, id):
        client = self.client
        event_name = 'delete_project'
        uri = '%s/event/fire_by_name/%s' % (self.cabochon_uri, event_name)
        client.send_message(dict(id=id), uri)
