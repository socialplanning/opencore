from Products.Five.viewlet.manager import ViewletManagerBase
from opencore.browser.topnav.topnav_menuitem import BaseMenuItem
from zope.viewlet.metaconfigure import viewletDirective
from zope.interface import Interface
from Acquisition import Explicit


class TopnavManager(ViewletManagerBase):
    """custom menu manager for opencore topnavigation"""

    def filter(self, viewlets):
        """also filter out viewlets by containment"""
        viewlets = super(TopnavManager, self).filter(viewlets)
        return [result for result in viewlets\
                if result[1].filter()]

    def sort(self, viewlets):
        """Sort the viewlets.

        ``viewlets`` is a list of tuples of the form (name, viewlet).
        """
        # By default, use the standard Python way of doing sorting. Unwrap the
        # objects first so that they are sorted as expected.  This is dumb
        # but it allows the tests to have deterministic results.
        return sorted(viewlets, lambda x, y: cmp(aq_base(x[1].order), aq_base(y[1].order)))

    @classmethod
    def create_topnav_viewlet(cls, name, permission, url,
                              css_class='oc-topnav',
                              for_=Interface,
                              contained=Interface,
                              filter=lambda self: True, **kwargs):
        klass_name = "%s-%s" % (BaseMenuItem.__name__, str(name))
        attrs = dict(name=name,
                     item_url=url,
                     _css_class=css_class,
                     filter=filter,
                     contained=contained)
        return type(klass_name, (BaseMenuItem, Explicit), attrs)                

            
def oc_menuitem_directive(_context, name, permission, url, *args, **kw):
    """create a class specific for viewlet"""
    new_keyword_args = kw.copy()
    viewlet_factory = TopnavManager.create_topnav_viewlet(name, permission,  url, *args, **kw)
    new_keyword_args['class_'] = viewlet_factory
    viewletDirective(_context, name, permission, **new_keyword_args)
