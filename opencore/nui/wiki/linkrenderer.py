from Acquisition import aq_inner
from wicked.at.link import BasicFiveLink
from plone.memoize.instance import memoize
import urllib

class LinkRenderer(BasicFiveLink):
    @memoize
    def add_url(self):
        return aq_inner(self.context).absolute_url()

    def add_link(self):
        """ replaces::
        #$here_url/@@add-page?title=${view/chunk}&section=${view/section}&referring=${here/UID}
        """
        args = dict(title=self.chunk,
                    section=self.section)
        return "%s/@@add-page?%s" %(self.add_url(), urllib.urlencode(args.items()))

