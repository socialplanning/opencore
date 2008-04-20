from zope.contentprovider.interfaces import IContentProvider
from zope.interface import implements
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class TeamFeed(object):
    implements(IContentProvider)

    def update(self):
        pass

    render = ZopeTwoPageTemplateFile('extra_feeds.pt')
