from lxml.html import fromstring
from lxml.html.clean import Cleaner
from interfaces import ICleanHtml
from opencore.nui.wiki.view import tounicode
from opencore.utility.interfaces import IProvideSiteConfig
from zope.component import getUtility
from zope.interface import implements
import copy

class HtmlCleaner(object):
    implements(ICleanHtml)

    def clean(self, html):
        config = getUtility(IProvideSiteConfig)
        whitelist = config.get('embed_whitelist', default='').split(',')
        whitelist = [ x.strip() for x in whitelist if x.strip() ]

        cleaner = Cleaner(host_whitelist=whitelist, safe_attrs_only=False)
        
        # stolen from lxml.html.clean
        if isinstance(html, basestring):
            return_string = True
            doc = fromstring(html)
        else:
            return_string = False
            doc = copy.deepcopy(html)
        cleaner(doc)
        if return_string:
            return tounicode(doc)
        else:
            return doc
