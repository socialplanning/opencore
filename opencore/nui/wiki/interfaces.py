from zope.interface import Interface, Attribute

class IReversionEvent(Interface):
    """marker for a reversion event"""
    reversion_message = Attribute('reversion message')
    old_history = Attribute('history of former head object')
    rollback_author = Attribute('user id of user doing rollback')

class IWikiHistory(Interface):
    """api to retrieve cache of history data for performance"""

    def __iter__(self):
        """yield objects containing version data"""

    def __len__(self):
        """return number of history items"""

    def __getitem__(self, version_id):
        """return particular revision data"""

    def new_history_item(self):
        """moves the cache over from the previous revision to the live object"""
