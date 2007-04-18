from Products.listen.content.mailinglist import MailingList
from Products.listen.permissions import InviteSubscribers
from Products.OpenPlans.config import PROJECTNAME

from Products.CMFCore import permissions as CMFPermissions
from Products.listen import permissions

from zope.interface import implements

from interfaces import IOpenMailingList
from fieldproperty import ListNameFieldProperty

PKG_NAME = 'listen'

factory_type_information = ( {
    'id'             : 'Open Mailing List',
    'icon'           : 'mailboxer_icon.png',
    'meta_type'      : 'OpenMailingList',
    'description'    : "A mailing list manages user subscriptions and "\
                       "processes incoming mail",
    'product'        : PROJECTNAME,
    'factory'        : 'addOpenMailingList',
    'immediate_view' : 'edit',
    'aliases'        : {'(Default)'     :'mailinglist_view',
                        'index.html'    :'mailinglist_view',
                        'view'          :'mailinglist_view',
                        'sharing'       :'folder_localrole_form',
                        'subscribers'   :'@@editAllSubscribers',
                        'edit'          :'@@edit'},
    'actions'        : (
                        {
                        'id': 'view',
                        'name': 'View',
                        'action': 'string:${object_url}',
                        'permissions': (CMFPermissions.View,)
                        },
                        {
                        'id': 'edit',
                        'name': 'Edit',
                        'action': 'string:${object_url}/edit',
                        'permissions': (permissions.EditMailingList,)
                        },
                        {
                        'id': 'search_archive',
                        'name': 'Search',
                        'action': 'string:${object_url}/archive/search_archive',
                        'permissions': (CMFPermissions.View,)
                        },
                        {
                        'id': 'archive',
                        'name': 'Archive',
                        'action': 'string:${object_url}/archive',
                        'permissions': (CMFPermissions.View,)
                        },
                        {
                        'id': 'membership',
                        'name': 'Membership',
                        'action': 'string:${object_url}/manage_membership',
                        'permissions': (permissions.EditMailingList,)
                        },
                        {
                        'id': 'moderation',
                        'name': 'Moderation',
                        'action': 'string:${object_url}/moderation',
                        'permissions': (permissions.EditMailingList,)
                        },
                       ),
    'filter_content_types' : True,
    'allowed_content_types' : (),
    'global_allow' : True,
    'allow_discussion' : False,
  },
)

fti = factory_type_information[0].copy()


def addOpenMailingList(self, id, title=u''):
    """ Add an OpenMailingList """
    o = OpenMailingList(id, title)
    self._setObject(id, o)

class OpenMailingList(MailingList):
    """
    Some OpenPlans specific tweaks to listen mailing lists.
    """
    implements(IOpenMailingList)

    portal_type = "Open Mailing List"
    meta_type = "OpenMailingList"

    mailto = ListNameFieldProperty(IOpenMailingList['mailto'])



from Products.listen.utilities.token_to_email import MemberToEmail
from Products.CMFCore.utils import getToolByName

def oc__init__(self, context):
    """
    Overrides the regular MemberToEmail to provide a more efficient way
    of finding the id for a given email for the opencore stack
    which uses membrane for user management.
    """
    self.context = context
    self.mtool = getToolByName(context, 'membrane_tool')
    
def oc_to_memberid(self, email):
    mems = self.mtool(getEmail=email)
    if mems:
        return mems[0].getId
    else:
        return None


def oc_lookup_memberid(self, member_id):
    member_obj = self.mtool(getID=member_id)
    
    if member_obj: 
        return member_obj[0].getEmail
    else:
        return None
    
        
MemberToEmail.__init__ = oc__init__
MemberToEmail.to_memberid = oc_to_memberid
MemberToEmail._lookup_memberid = oc_lookup_memberid
