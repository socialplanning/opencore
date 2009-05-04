from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.listen.content.mailinglist import MailingList
from fieldproperty import ListNameFieldProperty
from interfaces import IOpenMailingList
from opencore.configuration import PROJECTNAME
from zope.interface import implements
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter

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

    def manage_event(self, event_codes, headers):
        """ Handle event conditions passed up from smtp2zope.
        
            Primarily this method will be called by XMLRPC from smtp2zope.
            Copied from mailboxer to avoid having to acquire the mail template
            but instead try to get templates for them
        
        """
        for code in event_codes:
            from_ = headers.get('from')
            if from_ is None:
                continue
            view = queryMultiAdapter((self, self.REQUEST), name='event_template_sender_%d' % code)
            if view is None:
                view = getMultiAdapter((self, self.REQUEST), name='event_template_sender_default')
            msg = view(code, headers)
            returnpath = self.getValueFor('returnpath') or self.manager_email
            self._send_msgs([from_], msg, returnpath)
