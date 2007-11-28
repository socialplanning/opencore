from opencore.browser.topnav.topnav_menuitem import BaseMenuItem
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


#class ITopnavMenuItemSchema(IViewletDirective):
class ITopnavMenuItemSchema(Interface):
    """schema for topnav menu item configuration"""
    # can add title, description, required to schema
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
        description=_("When generating url, join this part of the url with the context"),
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

# could not get this to work properly
#     template = Path(
#         title=_("Content-generating template."),
#         description=_("Refers to a file containing a page template (should "
#                       "end in extension ``.pt`` or ``.html``)."),
#         required=False,
#         )

    sort_order = TextLine(
        title=_("Sort index"),
        description=_("Index used to determine viewlet order"),
        required=True,
        )

# this allows extra fields in configure to get passed through
ITopnavMenuItemSchema.setTaggedValue('keyword_arguments', True)
