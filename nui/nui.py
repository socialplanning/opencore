"""functions and variables for site-wide ui"""

# XXX this is shit. -egj, mp

windowTitleSeparator = ' :: '
logoURL = '++resource++img/logo.gif'


def renderTranscluderLink(viewname):
    return '<a href="@@%s" rel="include">%s</a>\n' % (viewname, viewname)

def renderOpenPage(page):
    return page.CookedBody()

def renderView(view):
    return view()
