from Products.CMFCore.utils import getToolByName
from opencore.interfaces import IOpenPage
from opencore.feed.base import BaseFeedAdapter
from opencore.feed.interfaces import IFeedData
from opencore.feed.interfaces import IFeedItem
from zope.component import adapts
from zope.component import createObject
from zope.interface import alsoProvides
from zope.interface import implements

class PageFeedAdapter(BaseFeedAdapter):
    """feed for wiki page modifications"""
    
    implements(IFeedData)
    adapts(IOpenPage)

    @property
    def items(self):
        if hasattr(self,'_items'):
            # If the property already contains something, there's no need to
            # regenerate it.
            return self._items

        pr = getToolByName(self.context, 'portal_repository')
        self._items = []
        for version in pr.getHistory(self.context, countPurged=False):
            description = version.comment
            page = version.object
            title = page.Title()
            link = page.absolute_url()
            pubDate = page.modified()
            author = version.sys_metadata.get('principal')

            self.add_item(title=title,
                          description=description,
                          link=link,
                          author=author,
                          pubDate=pubDate)
        return self._items
