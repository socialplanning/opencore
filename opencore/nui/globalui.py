"""functions and variables for site-wide ui"""

windowTitleSeparator = ' :: '
logoURL = '++resource++img/logo.gif'


def renderOpenPage(self, page):
    return page.CookedBody()

def wrapWithTag(towrap, tag, id=None):
    opening = id and '<%s id="%s">' % (tag, id) or '<%s>' % tag
    closing = '</%s>' % tag
    return '\n'.join((opening, towrap, closing))

