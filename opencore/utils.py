"""
opencore helper functions
"""
from Acquisition import aq_base
from Acquisition import aq_chain
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from zope.app.component.hooks import getSite
from zope.app.component.hooks import setSite
from zope.app.component.interfaces import ISite
from zope.component import getUtility

oc_props_id = 'opencore_properties'

def get_opencore_property(prop, context=None):
    """
    Returns a value from the opencore_properties property sheet.

    o prop - name of the property to retrieve

    o context - context object from which to acquire the properties tool;
                will use getSite if this isn't provided

    This function is very forgiving; if it can't retrieve the property
    because either the tool or the property don't exist, it returns
    None.
    """
    if context is None:
        # getSite returns the lowest level ISite object that has been
        # traversed in the current request
        context = getSite()
    pprops = getToolByName(context, 'portal_properties', None)
    if pprops is None:
        return
    oc_props = pprops._getOb(oc_props_id, None)
    if oc_props is None:
        return
    value = oc_props.getProperty(prop)
    if hasattr(aq_base(value), 'strip'):
        # strip whitespace from string property values
        value = value.strip()
    return value

def set_opencore_properties(context=None, **kw):
    """
    Sets the value of a set of properties on the opencore_properties
    sheet.

    o context - context object for acquiring the properties tool;
                getSite will be used if this isn't provided

    o kw=val - kw is the property name, val is the property value

    Unlike get_opencore_property, this isn't forgiving; you can't set
    a property unless you can get to the property sheet.
    """
    if context is None:
        # getSite returns the lowest level ISite object that has been
        # traversed in the current request
        context = getSite()
    pprops = getToolByName(context, 'portal_properties')
    oc_props = pprops._getOb(oc_props_id)
    return oc_props.manage_changeProperties(**kw)

def interface_in_aq_chain(obj, iface):
    """
    climbs obj's aq chain looking for any parent that provides iface

    returns the parent, if found, None if not
    """
    for parent in aq_chain(obj):
        if iface.providedBy(parent):
            return aq_inner(parent)

def get_utility_for_context(iface, context):
    """
    does a getSite / setSite dance to get the utility in the given
    context since five.localsitemanager has a bug which makes using
    getUtility's context argument fail
    """
    new_site = interface_in_aq_chain(context, ISite)
    orig_site = getSite()
    setSite(new_site)
    utility = getUtility(iface) # may raise an exception, this is okay
    setSite(orig_site)
    return utility
