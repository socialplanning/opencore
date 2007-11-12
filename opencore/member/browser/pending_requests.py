from zope.interface import implements
from zope.component import adapts
from zope.app.annotation.interfaces import IAnnotatable
from zope.app.annotation.interfaces import IAnnotations

from BTrees.OOBTree import OOBTree

from opencore.interfaces.pending_requests import IPendingRequests

annot_key = 'opencore.member.pending_requests' #planning for future

class PendingRequests(object):
    """
    Simple IPendingRequests implementation which stores pending requests
    as an annotation on the requester object consisting of a list of
    project ids as strings.
    
    This is done as simply as possible, so it just adapts any annotatable
    object; there are no sanity checks to ensure that only member objects
    can have requests stored on them, nor that ids refer to existing
    projects.
    """
    adapts(IAnnotatable)
    implements(IPendingRequests)

    def __init__(self, context):
        self.context = context
        annot = IAnnotations(context)
        req_annot = annot.get(annot_key, None)
        if req_annot is None:
            req_annot = set()
            annot[annot_key] = req_annot
        self._req_store = req_annot

    def getRequests(self):
        return tuple(self._req_store)
        
    def addRequest(self, proj_id):
        self._req_store.add(proj_id)

    def removeRequest(self, proj_id):
        self._req_store.remove(proj_id)

    def removeAllRequestsForUser(self):
        self._req_store.clear()
