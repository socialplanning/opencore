from zope.contentprovider.interfaces import IContentProvider
from zope.interface import implements
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class TeamFeed(object):
    implements(IContentProvider)

    def __init__(self, context, request, view):
        self.context = context
        self.request = request
        self.view = view

    def update(self):
        pass

    def render(self):
        return self.context.restrictedTraverse('teamfeed')()
