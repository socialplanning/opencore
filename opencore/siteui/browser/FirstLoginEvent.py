from Products.CMFCore.utils import getToolByName 
from zope.interface import implements

class FirstLoginEvent():
    implements(IFirstLoginEvent)
    def __init__(self, member):
        self.member = member
