from zope.interface import implements
from zope.app.annotation import IAnnotations

import DateTime
from BTrees.OOBTree import OOBTree
from OFS.SimpleItem import SimpleItem

from opencore.nui.project.interfaces import IEmailInvites

class EmailInvites(SimpleItem):
    """
    IEmailInvites local utility implementation.  Does no sanity
    checking of email addresses or project ids, just takes the
    information provided and stores / retrieves it.
    """
    implements(IEmailInvites)

    def __init__(self):
        self._by_address = OOBTree()
        self._by_project = OOBTree()

    def getInvitesByEmailAddress(self, address):
        return self._by_address.get(address, OOBTree())

    def getInvitesByProject(self, proj_id):
        return self._by_project.get(proj_id, OOBTree())

    def addInvitation(self, address, proj_id):
        now = DateTime.now()
        by_address = self.getInvitesByEmailAddress(address)
        if proj_id not in by_address:
            by_address[proj_id] = now
            self._by_address[address] = by_address

        by_project = self.getInvitesByProject(proj_id)
        if address not in by_project:
            by_project[address] = now
            self._by_project[proj_id] = by_project

    def removeInvitation(self, address, proj_id):
        by_email = self.getInvitesByEmailAddress(address)
        if proj_id in by_email:
            by_email.pop(proj_id)
            self._by_address[address] = by_email

        by_project = self.getInvitesByProject(proj_id)
        if address in by_project:
            by_project.pop(address)
            self._by_project = by_project

    def removeAllInvitesForAddress(self, address):
        by_email = self.getInvitesByEmailAddress(address)[:]
        for proj_id in by_email:
            self.removeInvitation(address, proj_id)
