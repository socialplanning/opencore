import feedparser
import lxml.etree
import urllib2
from dateutil.parser import parse
from opencore.browser.base import BaseView

def date_cmp(entry1, entry2):
    """compare feed entries by date"""
    return cmp(parse(entry1.date), parse(entry2.date))
        

class WordPressFeedView(BaseView):
    """a view for wordpress's feeds"""
    # XXX this should probably go back in latest_activity ::sigh::


    def handle_request(self):

        uri = self.request.get('uri').rstrip('/') # the base uri of wordpress
        n = self.request.get('n', 5)
        
        if uri:
            self.feed = feedparser.parse('%s/feed' % uri)
            comments = feedparser.parse('%s/comments/feed' % uri)

            # these could be handled in a unified way
            try:
                title = self.feed.feed.title
            except AttributeError:
                # this means the uri is not a feed (or something?)
                delattr(self, 'feed')
                return
            self.title = self.request.get('title', title)
            self.subtitle = self.request.get('subtitle', self.title)            


            # sort comments to entries
 #           entry_urls = {}
            for entry in self.feed.entries:

                # parse the whole page
                element =  lxml.etree.parse(urllib2.urlopen(entry.link), lxml.etree.HTMLParser())

                # find the comment id element
                entry.comment_string = element.xpath(".//*[@id='comments']")[0].text.strip()
 #               entry.comment_links = []
 #               entry_urls[entry.link] = entry             
 #           for comment in comments.entries:
 #               url = comment.link.rsplit('#comment',1)[0] # horrible hack
 #               try:
 #                   entry_urls[url].comment_links.append(url)
 #               except KeyError:
 #                   from pprint import pprint
 #                   import pdb;  pdb.set_trace()



            # annote members onto the entries
            membrane_tool = self.get_tool('membrane_tool')
            for entry in self.feed.entries:
                members = membrane_tool(id=self.feed.entries[0].author)
                if len(members) == 1:
                    entry.member = members[0].getObject() # XXX necessary to keep track of these?
                    entry.author_portrait = self.member_info_for_member(entry.member)['portrait_thumb_url']
                else:
                    entry.member = None
                    entry.author_portrait = '++resource++img/default-portrait-thumb.gif'                

#            self.feed.entries.sort(cmp=date_cmp) # they appeared sorted already?
            self.feed.entries = self.feed.entries[:n] # XXX could do earlier?

