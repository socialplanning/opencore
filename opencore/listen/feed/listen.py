import re

from opencore.featurelets.interfaces import IListenContainer
from opencore.feed.base import BaseFeedAdapter
from opencore.feed.base import FeedItemResponses
from opencore.feed.interfaces import IFeedData
from opencore.listen.interfaces import IOpenMailingList
from Products.listen.interfaces import ISearchableArchive
from Products.listen.lib.browser_utils import messageStructure
from zope.component import adapts
from zope.component import getUtility
from zope.interface import implements

# regular expression to strip names from an email
# address in standard format
email_re = re.compile(r' *"(.*)" *<.*@.*>')

def latest_reply(archive, message):
    """given a message, get the latest reply in the thread"""
    replies = archive.getMessageReferrers(message.message_id)
    if replies:
        return replies[0]
    return message

class ListsFeedAdapter(BaseFeedAdapter):
    implements(IFeedData)
    adapts(IListenContainer)

    title = 'Discussions'

    @property
    def mlists(self):
        return self.context.objectIds()

    def threads(self, mlist):
        archive = getUtility(ISearchableArchive, context=mlist)
        threads = archive.getToplevelMessages()        

    @property
    def items(self, n_items=5):
        """we aggregate the most recent messages across all mailing lists,
           then sort those by date and take the top n_items

           XXX this is potentially an expensive operation
           we may want a separate catalog on the lists level
           or store the mail messages in the main portal catalog as well
           in which case we would be able to search for messages
           in the site wide search"""

        if hasattr(self,'_items'):
            # If the property already contains something, there's no need to
            # regenerate it.
            return self._items

        messages = []
        mlists = self.mlists
        n_lists = len(mlists)
        for ml_id in mlists:
            mlist = self.context._getOb(ml_id)
            archive = getUtility(ISearchableArchive, context=mlist)
            threads = archive.getToplevelMessages()
            threads = [ dict(message=message, 
                             reply=latest_reply(archive, message), 
                             mlist=mlist)
                         for message in threads ]
            messages.extend(threads)
            
        date = lambda x: x['reply'].modification_date
        messages.sort(key=date, reverse=True)
        messages = messages[:n_items]

        self._items = []
        for message in messages:            
            reply = message['reply']
            mlist = message['mlist']
            message = message['message']

            structure = messageStructure(message,
                                         sub_mgr=mlist)
            reply_structure = messageStructure(reply,
                                               sub_mgr=mlist)
            
            link = '%s/forum_view' % structure['url'].rstrip('/')
            reply_url = '%s#%s' % ( link, reply_structure['id'] )

            pubDate = reply.modification_date
            
            author = reply_structure['from_id']
            if not author:
                author = reply_structure['mail_from']
                match = re.match(email_re, author)
                if match:
                    author = match.groups()[0]

            title = structure['subject']
            description = structure['subject']

            # if more than one mailing list, it should be noted
            context = None
            if n_lists > 1:
                context = { 'title': mlist.title,
                            'link': mlist.absolute_url }

            # deal with responses
            responses = message.responses
            if responses:
                byline = 'latest by'
                response = FeedItemResponses(responses, reply_url)
            else:
                response = None
                byline = 'by'

            self.add_item(title=title,
                          description=description,
                          link=link,
                          author=author,
                          pubDate=pubDate,
                          context=context,
                          byline=byline,
                          responses=response)
        return self._items


#XXX duplication between this class and lists class above
# can factor out common behavior to a separate function/superclass
# OR (better) can make the MailingListsFeed consume and aggregate the MailingListFeed
class MailingListFeedAdapter(BaseFeedAdapter):
    implements(IFeedData)
    adapts(IOpenMailingList)

    @property
    def items(self, n_items=5):
        """feed for latest messages in a mailing list"""

        if hasattr(self,'_items'):
            # If the property already contains something, there's no need to
            # regenerate it.
            return self._items

        archive = getUtility(ISearchableArchive, context=self.context)
        messages = archive.getToplevelMessages()
        messages = [ dict(message=message, 
                          reply=latest_reply(archive, message), 
                          mlist=self.context)
                     for message in messages ]

        date = lambda x: x['reply'].modification_date
        messages.sort(key=date, reverse=True)
        messages = messages[:n_items]

        self._items = []
        for message in messages:            
            reply = message['reply']
            mlist = message['mlist']
            message = message['message']

            structure = messageStructure(message,
                                         sub_mgr=mlist)
            reply_structure = messageStructure(reply,
                                               sub_mgr=mlist)
            
            link = '%s/forum_view' % structure['url'].rstrip('/')
            reply_url = '%s#%s' % ( link, reply_structure['id'] )

            pubDate = reply.modification_date
            
            author = reply_structure['from_id']
            if not author:
                author = reply_structure['mail_from']
                match = re.match(email_re, author)
                if match:
                    author = match.groups()[0]

            title = structure['subject']
            description = structure['subject']

            # deal with responses
            responses = message.responses
            if responses:
                byline = 'latest by'
                response = FeedItemResponses(responses, reply_url)
            else:
                response = None
                byline = 'by'

            self.add_item(title=title,
                          description=description,
                          link=link,
                          author=author,
                          pubDate=pubDate,
                          byline=byline,
                          responses=response)
        return self._items
