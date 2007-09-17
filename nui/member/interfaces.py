# move to opencore.interfaces
from zope.interface import Interface

class ITransientMessage(Interface):
    """add/list/remove messages intended for the user that can be removed"""

    def store(mem_id, category, msg):
        """store a msg for a particular user in a category"""

    def get_msgs(mem_id, category):
        """return an iterable of all messages for a user in a category
        
           each message returned is a (idx, msg)"""

    def get_all_msgs(mem_id):
        """return an iterable of all messages for a user
        
           each message returned is a (idx, msg)"""

    def pop(mem_id, category, idx):
        """remove and return the message for the member, category, and index"""

