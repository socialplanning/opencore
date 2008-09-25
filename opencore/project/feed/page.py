from AccessControl import getSecurityManager
from Globals import get_request
from opencore.feed.interfaces import IFeedData

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
    link = page.absolute_url()
    pubDate = page.modified()
    author = getSecurityManager().getUser().getId()
    feed.add_item(title=title,
                  description=description,
                  link=link,
                  author=author,
                  pubDate=pubDate)
