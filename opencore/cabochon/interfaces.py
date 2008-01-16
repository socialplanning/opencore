from zope.interface import Interface

class ICabochonClient(Interface):
    def __init__(self, conf):
        pass

    def notify_project_deleted(self, id):
        """send a project deleted message to cabochon"""
