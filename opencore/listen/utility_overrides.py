import os
from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces.utilities import IHeaderValidator
from Products.listen.utilities.token_to_email import MemberToEmail
from Products.membrane.config import TOOLNAME as MBTOOLNAME
from zope.interface import implements

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

from opencore.configuration import utils as conf_utils
from libopencore.mail_headers import validate_headers as _validate_headers
def get_secret_filename():
    filename = conf_utils.product_config('listen_secret_filename', 'opencore.listen')
    if not filename:
        filename = os.path.join(os.environ.get('INSTANCE_HOME', 'listen_secret.txt'))
    return filename

class OpencoreHeaderValidator(object):
    implements(IHeaderValidator)
    
    def validate_headers(self, headers):
        return _validate_headers(headers, get_secret_filename())

    def clean_headers(self, headers):
        if 'x-opencore-validation-key' in headers:
            del headers['x-opencore-validation-key']
        return headers
