import feedparser
import lxml.etree
import urllib2
from dateutil.parser import parse
from opencore.browser.base import BaseView

def date_key(entry):
    return parse(entry.date)

class WordPressFeedView(BaseView):
    """a view for wordpress's feeds"""
    # XXX this should probably go back in latest_activity ::sigh::

    def handle_request(self):

        uri = self.request.get('uri').rstrip('/') # the base uri of wordpress
        n = self.request.get('n', 5)

        if uri:

            # without the trailing slash, one gets different results!
            # ssee http://trac.openplans.org/openplans/ticket/2197#comment:3
            self.feed = feedparser.parse('%s/feed/' % uri)

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
            for entry in self.feed.entries:

                # parse the whole page
                element =  lxml.etree.parse(urllib2.urlopen(entry.link), lxml.etree.HTMLParser())

                # find the comment id element
                entry.comment_string = element.xpath(".//*[@id='comments']")[0].text.strip()
 


            # annote members onto the entries
            membrane_tool = self.get_tool('membrane_tool')
            for entry in self.feed.entries:
                members = membrane_tool(getId=entry.author)
                if len(members) == 1:
                    entry.member = members[0].getObject() # XXX necessary to keep track of these?
                    entry.author_portrait = self.member_info_for_member(entry.member)['portrait_thumb_url']
                else:
                    entry.member = None
                    entry.author_portrait = '++resource++img/default-portrait-thumb.gif'                

#            self.feed.entries.sort(key=date_key) # they appeared sorted already?
            self.feed.entries = self.feed.entries[:n] # XXX could do earlier?

