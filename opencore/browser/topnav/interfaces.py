from opencore.interfaces.adding import IAddProject
from opencore.interfaces.adding import IAmAPeopleFolder
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.interface import Interface
from zope.schema import TextLine
from zope.viewlet.interfaces import IViewletManager
from zope.viewlet.metadirectives import IViewletDirective
from zope.configuration.fields import GlobalObject
from zope.configuration.fields import Path

# these functions control viewlet behavior

class ITopnavMenuItems(IViewletManager):
    """Viewlets for the context topnav menu"""


class ITopnavMenuItemSchema(Interface):
    """schema for topnav menu item configuration
       really a superset of IViewletDirective, but we have defaults
       for permission, class, and template, so we don't require those"""

    sort_order = TextLine(
        title=(u"Sort index"),
        description=(u"Index used to determine viewlet order"),
        required=True,
        )

    text = TextLine(
        title=(u"Menu item text"),
        description=(u"Text that the menu item display. Defaults to name"),
        required=False,
        )
    
    filter = GlobalObject(
        title=(u'Should viewlet render'),
        description=(u'Predicate function to filter inclusion in menu.'),
        required=False,
        )
    
    class_ = GlobalObject(
        title=(u"Viewlet Class"),
        description=(u"Viewlet class for topnav menu items."),
        required=False,
        )

    container = GlobalObject(
        title=(u'Containment Interface'),
        description=(u'Interface required of container to display menu item'),
        required=False,
        )

    css_class = GlobalObject(
        title=(u'Button css class'),
        description=(u'function that returns css class to apply when button'
                       'is selected'),
        required=False,
        )

    item_url = TextLine(
        title=(u'Relative item url'),
        description=(u"When generating url, join this part of the url with the"
                      "context"),
        required=False,
        )

    url = GlobalObject(
        title=(u'Menu item url'),
        description=(u'Where the menu item links to'),
        required=False,
        )

    selected = GlobalObject(
        title=(u'Test if selected'),
        description=(u'Predicate function to check if menu item is selected'),
        required=False,
        )

# this allows extra fields in configure to get passed through
ITopnavMenuItemSchema.setTaggedValue('keyword_arguments', True)
