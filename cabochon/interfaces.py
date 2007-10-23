from zope.interface import Interface

class ICabochonClient(Interface):
    def __init__(self, conf):
        pass

    def queue(self, queue):
        pass
