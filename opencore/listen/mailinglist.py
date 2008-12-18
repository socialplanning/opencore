from Products.CMFCore import permissions as CMFPermissions
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.listen import permissions
from Products.listen.content.mailinglist import MailingList
from Products.listen.permissions import InviteSubscribers
from fieldproperty import ListNameFieldProperty
from interfaces import IOpenMailingList
from opencore.configuration import PROJECTNAME
from zope.interface import implements

PKG_NAME = 'listen'

# XXX We can probably delete this FTI, it's from when we used the plone UI.
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

class OpenMailingList(MailingList, DefaultDublinCoreImpl):
    """
    Some OpenPlans specific tweaks to listen mailing lists.
    """
    implements(IOpenMailingList)

    portal_type = "Open Mailing List"
    meta_type = "OpenMailingList"
    creator = ""

    mailto = ListNameFieldProperty(IOpenMailingList['mailto'])

    # this overrides MailBoxer's limit of 10 emails in 10 minutes
    # so now, up to 100 emails are allowed in 10 minutes before the
    # sender is disabled
    senderlimit = 100
