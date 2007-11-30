from Acquisition import aq_base
from opencore.browser.topnav.viewlet import contained_item_url
from opencore.browser.topnav.viewlet import nofilter
from opencore.browser.topnav.viewlet import default_css
from opencore.browser.topnav.viewlet import if_request_starts_with_url
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five.viewlet.manager import ViewletManagerBase
from Products.Five.viewlet.metaconfigure import viewletDirective
from Products.Five.viewlet.viewlet import ViewletBase

class TopnavManager(ViewletManagerBase):
    """custom menu viewlet manager for opencore topnav"""

    def filter(self, viewlets):
        """give viewlets the chance to opt out of rendering"""
        return [result for result in super(TopnavManager, self).filter(viewlets)
                if result[1].filter()]

    def sort(self, viewlets):
        """Sort the viewlets.
           All topnav menuitems have a sort_order attribute, which will specify
           the ordering"""
        return sorted(
            viewlets,
            lambda x, y: cmp(aq_base(x[1].sort_order), aq_base(y[1].sort_order)))

    @classmethod
    def create_topnav_viewlet(cls, name, sort_order,
                              text,
                              url,
                              item_url,
                              filter,
                              container,
                              css_class,
                              selected,
                              template,
                              **kw
                              ):
        """factory function that creates viewlet classes
           based on configuration"""
        # set the name to help when getting a repr on the object"""
        klass_name = "%s-%s" % (ViewletBase.__name__, str(name))
        attrs = dict(name=name,
                     text=text,
                     sort_order=sort_order,
                     url=url,
                     item_url=item_url,
                     filter=filter,
                     container=container,
                     css_class=css_class,
                     selected=selected,
                     render=template,
                     )
        return type(klass_name, (ViewletBase,), attrs)                

            
def oc_menuitem_directive(_context, name, sort_order,
                          text=None,
                          permission='zope2.View',
                          url=contained_item_url,
                          item_url=u'',
                          filter=nofilter,
                          container=IPloneSiteRoot,
                          css_class=default_css,
                          selected=if_request_starts_with_url,
                          template=None,
                          **kw):
    """create a class specific for viewlet, and register it"""
    new_keyword_args = kw.copy()
    if text is None:
        text = name
    if template is None:
        template = ZopeTwoPageTemplateFile('menuitem.pt')
    viewlet_factory = TopnavManager.create_topnav_viewlet(
        name,
        sort_order,
        text,
        url,
        item_url,
        filter,
        container,
        css_class,
        selected,
        template,
        )
    new_keyword_args['class_'] = viewlet_factory
    new_keyword_args['manager'] = TopnavManager
    viewletDirective(_context, name, permission, **new_keyword_args)
