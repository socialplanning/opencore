from Products.CMFCore.utils import getToolByName
from opencore.interfaces import IOpenPage
from opencore.feed.base import BaseFeedAdapter
from opencore.feed.interfaces import IFeedData
from opencore.feed.interfaces import IFeedItem
from zope.component import adapts
from zope.interface import alsoProvides
from zope.interface import implements

class PageFeedAdapter(BaseFeedAdapter):
    """feed for wiki page modifications"""
    
    implements(IFeedData)
    adapts(IOpenPage)

    @property
    def items(self):
        pr = getToolByName(self.context, 'portal_repository')
        for version in pr.getHistory(self.context, countPurged=False):
            description = version.comment
            page = version.object
            title = page.Title()
            link = page.absolute_url()
            pubDate = page.modified()
            #body = page.getText()
            feed_item = type('PageFeedItem',
                             (object,),
                             dict(title=title,
                                  description=description,
                                  link=link,
                                  pubDate=pubDate,
                                  #body=body,
                                  ))

            # to be technically correct
            alsoProvides(feed_item, IFeedItem)
            
            yield feed_item
