from zope.interface import implements

from opencore.cabochon.interfaces import ICabochonClient
from opencore.cabochon.config import event_queue_directory, event_server, \
     cabochon_username, cabochon_password
from cabochonclient import CabochonClient as Base
from threading import Thread
from zope.component import getUtility

class CabochonClient(Base):
    implements(ICabochonClient)
    def __init__(self):
        Base.__init__(self, event_queue_directory, event_server, username = cabochon_username, password=cabochon_password)
        sender = self.sender()
        t = Thread(target=sender.send_forever)
        t.setDaemon(True)
        t.start()
