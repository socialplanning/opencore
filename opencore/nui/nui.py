"""functions and variables for site-wide ui"""


windowTitleSeparator = ' :: '
logoURL = '++resource++img/logo.gif'


def renderTranscluderLink(viewname):
    return '<a href="@@%s" rel="include">%s</a>\n' % (viewname, viewname)

def renderOpenPage(page):
    return page.CookedBody()

def wrapWithTag(towrap, tag, id=None):
    opening = id and '<%s id="%s">' % (tag, id) or '<%s>' % tag
    closing = '</%s>' % tag
    return '\n'.join((opening, towrap, closing))

def renderView(view):
    return view.index()
