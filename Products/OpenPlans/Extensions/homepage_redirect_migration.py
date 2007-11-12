import re
from StringIO import StringIO
from Products.CMFCore.utils import getToolByName
from opencore.project.browser.interfaces import IHomePage

pat = 'http://[^/]*(.*)'
regex = re.compile(pat)

def homepage_redirect_migration(self):
    out = StringIO()
    portal = getToolByName(self, 'portal_url').getPortalObject()
    out.write('starting home page migration\n')
    for brain in portal.portal_catalog(portal_type='OpenProject'):
        proj = brain.getObject()
        hp = IHomePage(proj)
        cur_page = hp.home_page
        match_obj = regex.match(cur_page)
        if not match_obj:
            out.write('no match found for %s\n' % proj.getId())
            continue
        # XXX change dev to stage, www, etc as appropriate
        new_page = 'http://dev.nycstreets.org%s' % match_obj.group(1)
        hp.home_page = new_page
        proj._p_changed = True
        out.write('home page for %s changed to: %s\n' % (proj.getId(), new_page))
    out.write('done migrating\n')
    return out.getvalue()
