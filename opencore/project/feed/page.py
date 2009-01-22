from opencore.interfaces import IOpenPage
from opencore.feed.base import BaseFeedAdapter
from opencore.feed.interfaces import IFeedData
from opencore.nui.wiki.interfaces import IWikiHistory
from zope.component import adapts
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

        self._items = []

        # We use the fast IWikiHistory adapter to avoid prohibitively expensive
        # iteration over the repository for frequently edited pages. #2766
        for version in IWikiHistory(self.context):
            # XXX This is a regression: the old implementation
            # actually provided the title at the time of the revision,
            # but that's not stored in our history cache. See #2767
            title = self.context.Title()
            # Behavior changed deliberately while fixing #2766: we link to the
            # revision, rather than the current version of the page. - PW
            link = '%s/version?version_id=%s' % (self.context.absolute_url(),
                                                 version['version_id'])
            self.add_item(title=title,
                          description=version['comment'],
                          link=link,
                          author = version['author'],
                          pubDate=version['modification_date'])
        return self._items
