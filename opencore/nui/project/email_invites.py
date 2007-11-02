from zope.interface import implements
from zope.app.annotation import IAnnotations
from topp.utils.persistent import OOBTreeBag
from BTree.OOBTree import OOBTree
import DateTime
from OFS.SimpleItem import SimpleItem

from Products.CMFCore.utils import getToolByName

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
        return self._by_address.get(address, KeyedMap(key=(address, self)))

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
            self._by_project[proj_id] = by_project

    def removeAllInvitesForAddress(self, address):
        by_email = self.getInvitesByEmailAddress(address)[:]
        for proj_id in by_email:
            self.removeInvitation(address, proj_id)

    def convertInvitesForMember(self, member):
        address = member.getEmail()
        invites = self.getInvitesByEmailAddress(address)
        tmtool = getToolByName(self, 'portal_teams')
        wftool = getToolByName(self, 'portal_workflow')
        for proj_id in invites:
            tm = tmtool.getTeamById(proj_id)
            if tm is not None:
                mship = tm._createMembership(member)
                # bad touch, we have to make it look like someone
                # other than the actual user made the request, so
                # it'll be treated as an invitation :-(
                wf_id = wftool.getChainFor(mship)[0]
                wf_hist = mship.workflow_history.get(wf_id)
                wf_status = wf_hist[-1]
                wf_status['actor'] = 'admin'
                mship.from_email_invite = True
                mship.reindexObject()
                
            self.removeInvitation(address, proj_id)


class KeyedMap(OOBTreeBag):
    """simple btree ish mapping with it's own unique key"""
    def __init__(self, btree=None, key=None):
        self._data = btree
        if not btree: # for migration
            self._data = OOBTree()
        self.key = self.make_key(key)
        
    def make_key(self, input):
        return hash(self, input)
    
