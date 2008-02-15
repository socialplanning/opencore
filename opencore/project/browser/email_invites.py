from BTrees.OOBTree import OOBTree
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import getToolByName
from opencore.project.browser import utils
from opencore.interfaces.membership import IEmailInvites
from topp.utils.persistence import OOBTreeBag, KeyedMap
from zope.app.annotation import IAnnotations
from zope.interface import implements
import DateTime


class EmailInvites(SimpleItem):
    """
    IEmailInvites local utility implementation.  Does no sanity
    checking of email addresses or project ids, just takes the
    information provided and stores / retrieves it.

    @@ might be better to use UIDs for project ids
    """
    implements(IEmailInvites)

    def __init__(self, migrate_from=None):
        if migrate_from is not None:
            self._by_address = migrate_from._by_address
            self._by_project = migrate_from._by_project
        else:
            self._by_address = OOBTree()
            self._by_project = OOBTree()

    def getInvitesByEmailAddress(self, address):
        by_addy = self._by_address.get(address)
        if by_addy is not None:
            return by_addy
        key = utils.make_key()
        map = KeyedMap(key=key)
        self._by_address[address]=map
        return map
    getInvitesByEmailAddress = utils.bbb_keymap(wrap=True)(getInvitesByEmailAddress)

    def getInvitesByProject(self, proj_id):
        by_proj = self._by_project.get(proj_id)
        if by_proj is not None:
            return by_proj  
        return OOBTree()

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
        return by_address.key

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

    def removeAllInvitesForProject(self, proj_id):
        if not isinstance(proj_id, basestring):
            proj_id = proj_id.getId()
        if proj_id in self._by_project:
            del self._by_project[proj_id]

    def convertInviteForMember(self, member, address, proj_id):
        tmtool = getToolByName(self, 'portal_teams')
        wftool = getToolByName(self, 'portal_workflow')
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
        return mship

    def convertInvitesForMember(self, member):
        address = member.getEmail()
        invites = self.getInvitesByEmailAddress(address)
        mships = [self.convertInviteForMember(member, address, proj_id) for proj_id in invites]
        return mships
                


