from zope.interface import implements
from zope.component import adapts
from zope.app.annotation.interfaces import IAnnotatable
from zope.app.annotation.interfaces import IAnnotations

from BTrees.OOBTree import OOBTree
from Products.ATContentTypes.interface.folder import IATBTreeFolder

from opencore.interfaces.pending_requests import IPendingRequests
from opencore.interfaces.pending_requests import IRequestMembership

annot_key = 'opencore.member.pending_requests' #planning for future

# XXX todo we have to store the request msg as well as the proj id!
class PendingRequests(object):
    """
    Simple IPendingRequests implementation which stores pending requests
    as an annotation on the requester object consisting of a list of
    project ids as strings.
    """
    adapts(IAnnotatable, IATBTreeFolder)
    implements(IPendingRequests)

    def __init__(self, requester, folder):
        self.requester = requester
        self.folder = folder
        annot = IAnnotations(requester)
        req_annot = annot.get(annot_key, None)
        if req_annot is None:
            req_annot = set()
            annot[annot_key] = req_annot
        self._req_store = req_annot

    def getRequests(self):
        return tuple(self._req_store)
        
    def addRequest(self, proj_id):
        # trigger the exception if this doesn't exist or is inaccessible
        proj = getattr(self.folder, proj_id)
        self._req_store.add(proj_id)

    def removeRequest(self, proj_id):
        self._req_store.remove(proj_id)

    def removeAllRequestsForUser(self):
        self._req_store.clear()

    def _convertRequest(self, proj_id):
        proj = getattr(self.folder, proj_id)
        team = proj.getTeams()[0]
        return IRequestMembership(team).join()

    def convertRequests(self):
        reqs = self._req_store
        converted = []
        for proj_id in reqs:
            if self._convertRequest(proj_id):
                converted.append(proj_id)
        for proj_id in converted:
            reqs.remove(proj_id)
        return tuple(converted)
