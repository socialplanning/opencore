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
    'id'             : 'Mailing List',
    'icon'           : 'mailboxer_icon.png',
    'meta_type'      : 'MailingList',
    'description'    : "A mailing list manages user subscriptions and "\
                       "processes incoming mail",
    'product'        : PKG_NAME,
    'factory'        : 'addMailingList',
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
                        'id': 'archive',
                        'name': 'archive',
                        'action': 'string:${object_url}/archive',
                        'permissions': (CMFPermissions.View,)
                        },
# TODO: Moderation and bounced/disabled address management TTW
#                         {
#                         'id': 'moderate',
#                         'name': 'Moderate',
#                         'action': 'string:${object_url}/mqueue',
#                         'permissions': (permissions.ManageSubscriptions,)
#                         },
#                         {
#                         'id': 'managelist',
#                         'name': 'Manage List',
#                         'action': 'string:${object_url}/manage-list',
#                         'permissions': (permissions.ManageSubscriptions,)
#                         },
                        {
                        'id': 'subscribers',
                        'name': 'membership',
                        'action': 'string:${object_url}/manage_membership',
                        'permissions': (permissions.ManageSubscriptions,)
                        },
                       ),
    'filter_content_types' : True,
    'allowed_content_types' : (),
    'global_allow' : True,
    'allow_discussion' : False,
  },
)

fti = factory_type_information[0].copy()
fti['id'] = 'Open Mailing List'
fti['meta_type'] = "OpenMailingList"
fti['product'] = PROJECTNAME
fti['factory'] = 'addOpenMailingList'
# Add subscription invitation
fti['aliases']['invite'] = '@@inviteMembers'
fti['actions'] = fti['actions'] + (
    {'id': 'invite_members',
     'name': 'Invite Members',
     'action': 'string:${object_url}/invite',
     'permissions': (InviteSubscribers,)
     },)

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
