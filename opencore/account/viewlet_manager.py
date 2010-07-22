from opencore.browser.viewletmanagers import SortedViewletManager
from Products.Five.viewlet.manager import ViewletManagerBase
from zope.viewlet.interfaces import IViewletManager
from zope.interface import implements

class ICreateAccount(IViewletManager):
    """ form plugin for account registration """

class CreateAccountManager(ViewletManagerBase):
    """viewlet manager for project preferences """

    implements(ICreateAccount)
