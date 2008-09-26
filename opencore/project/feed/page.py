from AccessControl import getSecurityManager
from DateTime import DateTime
from Globals import get_request
from opencore.feed.interfaces import IFeedData
from opencore.utils import get_rel_url_for

def page_feed_listener(page, event):
    """
    event subscriber that adds items to a single wiki page's feed
    """
    req = get_request()
    if req is None:
        # try acquisition as a fail-over
        req = page.REQUEST
    feed = IFeedData(page)
    description = req.form.get('comment', '')
    title = page.Title()
    rel_link = get_rel_url_for(page)
    pubDate = DateTime()
    author = getSecurityManager().getUser().getId()
    feed.add_item(title=title,
                  description=description,
                  rel_link=rel_link,
                  author=author,
                  pubDate=pubDate)
