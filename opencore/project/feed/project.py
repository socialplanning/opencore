from Products.CMFCore.utils import getToolByName
from opencore.interfaces import IProject
from opencore.feed.base import BaseFeedAdapter
from opencore.feed.interfaces import IFeedData
from zope.component import adapts
from zope.interface import implements

class WikiFeedAdapter(BaseFeedAdapter):
    """feed for wiki page modifications in project"""
    
    implements(IFeedData)
    adapts(IProject)

    title = 'Pages'
 
    @property
    def link(self):
        # XXX this will become '%s/home'
        # how to get this?
        return '%s/project-home' % self.context.absolute_url()

    @property
    def items(self, n_items=5):
        if hasattr(self,'_items'):
            # If the property already contains something, there's no need to
            # regenerate it.
            return self._items

        cat = getToolByName(self.context, 'portal_catalog')
        brains = cat(portal_type='Document',
                     path='/'.join(self.context.getPhysicalPath()),
                     sort_on='modified',
                     sort_order='descending',
                     sort_limit=n_items)
        for brain in brains:
            title = brain.Title
            #XXX would be nice if the description was the revision note
            #we should index it that way
            description = brain.Description
            author = brain.lastModifiedAuthor
            link = brain.getURL()
            pubDate = brain.modified
            #XXX maybe we should stick the body in here as well?
            # the feed supports passing the "body" attribute
            # problem though, is that we don't want to put all of it in there
            # and if we cut it off, we might cut off some html
            # let's just leave it off for now
            #body = brain.getObject().getText()

            self.add_item(title=title,
                          description=description,
                          link=link,
                          author=author,
                          pubDate=pubDate,
                          byline='edited by')
        return self._items
