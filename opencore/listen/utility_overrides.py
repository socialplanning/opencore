from Products.CMFCore.utils import getToolByName
from Products.listen.utilities.token_to_email import MemberToEmail
from Products.membrane.config import TOOLNAME as MBTOOLNAME

class OpencoreMemberLookup(MemberToEmail):
    """ override searches to use the membrane tool """

    def __init__(self, context):
        self.context = context

    def _search(self, query_dict, prop):
        """ generic search method """
        mbtool = getToolByName(self.context, MBTOOLNAME)
        brains = mbtool(**query_dict)
        if brains:
            # assert we only got one result?
            brain = brains[0]
            return getattr(brain, prop)
        else:
            return None

    # these override the superclass methods
    def _lookup_memberid(self, member_id):
        query = dict(getId=member_id)
        return self._search(query, 'getEmail')

    def to_memberid(self, email):
        query = dict(getEmail=email)
        return self._search(query, 'getId')
