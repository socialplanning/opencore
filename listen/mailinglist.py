from Products.listen.content.mailinglist import MailingList
from Products.listen.content.mailinglist import factory_type_information \
     as base_fti
from Products.OpenPlans.config import PROJECTNAME

from zope.interface import implements

from interfaces import IOpenMailingList
from fieldproperty import ListNameFieldProperty

fti = base_fti[0].copy()
fti['id'] = 'Open Mailing List'
fti['meta_type'] = "OpenMailingList"
fti['product'] = PROJECTNAME
fti['factory'] = 'addOpenMailingList'

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
