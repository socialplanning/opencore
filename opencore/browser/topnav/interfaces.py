from opencore.i18n import _
from zope.interface import Interface
from zope.schema import TextLine
from zope.viewlet.interfaces import IViewletManager
from zope.viewlet.metadirectives import IViewletDirective
import zope.configuration.fields
from topp.utils import zutils


def contained(viewlet):
    return bool([result for result in viewlets\
                 if zutils.aq_iface(self.context, result[1].contained)])


class ITopnavMenuItems(IViewletManager):
    """Viewlets for the context topnav menu"""


class ITopnavMenuItemSchema(IViewletDirective):
    """schema for topnav menu item configuration"""
    # can add title, description, required to schema
    filter = zope.configuration.fields.GlobalObject(
        title=_("filter"),
        description=_("Function to filter inclusion in menu."),
        required=False,
        default=contained)
    
    contained = zope.configuration.fields.GlobalObject(
        title=_("Containment Interface"),
        description=_("Interface required of container to display menu item"),
        required=False,
        default=Interface) #@@ replace with IPloneSiteRoot

    

ITopnavMenuItemSchema.setTaggedValue('keyword_arguments', True)
