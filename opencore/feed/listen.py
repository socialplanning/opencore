from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import ISearchableArchive
from opencore.featurelets.interfaces import IListenContainer
from opencore.listen.interfaces import IOpenMailingList
from opencore.feed.base import BaseFeedAdapter
from opencore.feed.interfaces import IFeedData
from opencore.feed.interfaces import IFeedItem
from zope.component import adapts
from zope.component import getUtility
from zope.interface import alsoProvides
from zope.interface import implements

class ListsFeedAdapter(BaseFeedAdapter):
    implements(IFeedData)
    adapts(IListenContainer)

    @property
    def items(self):
        """we aggregate the 10 most recent messages across all mailing lists,
           then sort those by date and take the top 10

           XXX this is potentially an expensive operation
           we may want a separate catalog on the lists level
           or store the mail messages in the main portal catalog as well
           in which case we would be able to search for messages
           in the site wide search"""

        MSG_BODY_LENGTH = 300

        brains = []
        for ml_id in self.context.objectIds():
            sa = getUtility(
                ISearchableArchive,
                context=self.context._getOb(ml_id))
            ml_brains = sa.searchResults(sort_on='modification_date',
                                         sort_order='descending',
                                         sort_limit=10)
            brains.extend(ml_brains)

        brains = sorted(brains,
                        key=lambda x:x.modification_date,
                        reverse=True)
        brains = brains[:10]

        for brain in brains:
            #XXX
            # we get the object for now to see the body of the message
            # we can either add it to the metadata, or forget about it
            # or maybe something more clever?
            msg = brain.getObject()
            
            title = brain.subject
            # only put the first part of the body of long messages
            body = msg.body
            if len(body) > MSG_BODY_LENGTH:
                body = '%s ...' % body[:MSG_BODY_LENGTH-4]
            description = body
            link = brain.getURL()
            pubDate = brain.modification_date

            # returning a dictionary would also work
            # this is just more formal
            feed_item = type('MailFeedItem',
                             (object,),
                             dict(title=title,
                                  description=description,
                                  link=link,
                                  pubDate=pubDate,
                                  ))

            # to be technically correct
            alsoProvides(feed_item, IFeedItem)
            
            yield feed_item

#XXX duplication between this class and lists class above
# can factor out common behavior to a separate function/superclass
class MailingListFeedAdapter(BaseFeedAdapter):
    implements(IFeedData)
    adapts(IOpenMailingList)

    @property
    def items(self):
        """feed for list 10 messages in a mailing list

           XXX somewhat expensive in that we get 10 mailing list objects
           but I think that these are somewhat lightweight in that they
           inherit from OFS.Folder
           """

        MSG_BODY_LENGTH = 300

        brains = []
        sa = getUtility(
            ISearchableArchive,
            context=self.context)
        brains = sa.searchResults(sort_on='modification_date',
                                  sort_order='descending',
                                  sort_limit=10)

        for brain in brains:
            #XXX
            # we get the object for now to see the body of the message
            # we can either add it to the metadata, or forget about it
            # or maybe something more clever?
            msg = brain.getObject()
            
            title = brain.subject
            # only put the first part of the body of long messages
            body = msg.body
            if len(body) > MSG_BODY_LENGTH:
                body = '%s ...' % body[:MSG_BODY_LENGTH-4]
            description = body
            link = brain.getURL()
            pubDate = brain.modification_date

            # returning a dictionary would also work
            # this is just more formal
            feed_item = type('MailFeedItem',
                             (object,),
                             dict(title=title,
                                  description=description,
                                  link=link,
                                  pubDate=pubDate,
                                  ))

            # to be technically correct
            alsoProvides(feed_item, IFeedItem)
            
            yield feed_item
