from opencore.i18n import _
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


class ITopnavActions(IViewletManager):
    """Viewlets for the topnav actions"""


class ITopnavMenuItemSchema(Interface):
    """schema for topnav menu item configuration
       really a superset of IViewletDirective, but we have defaults
       for permission, class, and template, so we don't require those"""

    sort_order = TextLine(
        title=_("Sort index"),
        description=_("Index used to determine viewlet order"),
        required=True,
        )

    text = TextLine(
        title=_("Menu item text"),
        description=_("Text that the menu item display. Defaults to name"),
        required=False,
        )
    
    filter = GlobalObject(
        title=_('Should viewlet render'),
        description=_('Predicate function to filter inclusion in menu.'),
        required=False,
        )
    
    class_ = GlobalObject(
        title=_("Viewlet Class"),
        description=_("Viewlet class for topnav menu items."),
        required=False,
        )

    container = GlobalObject(
        title=_('Containment Interface'),
        description=_('Interface required of container to display menu item'),
        required=False,
        )

    css_class = GlobalObject(
        title=_('Button css class'),
        description=_('function that returns css class to apply when button'
                       'is selected'),
        required=False,
        )

    item_url = TextLine(
        title=_('Relative item url'),
        description=_("When generating url, join this part of the url with the"
                      "context"),
        required=False,
        )

    url = GlobalObject(
        title=_('Menu item url'),
        description=_('Where the menu item links to'),
        required=False,
        )

    selected = GlobalObject(
        title=_('Test if selected'),
        description=_('Predicate function to check if menu item is selected'),
        required=False,
        )

# this allows extra fields in configure to get passed through
ITopnavMenuItemSchema.setTaggedValue('keyword_arguments', True)
