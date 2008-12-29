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
