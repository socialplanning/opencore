"""
opencore helper functions
"""
from Acquisition import aq_base
from Acquisition import aq_chain
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from opencore.utility.interfaces import IProvideSiteConfig
from zope.app.component.hooks import getSite
from zope.app.component.hooks import setSite
from zope.app.component.interfaces import ISite
from zope.component import getUtility

import time

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
    (including obj)

    returns the matching object, if found; otherwise None.
    """
    for parent in aq_chain(obj):
        if iface.providedBy(parent):
            return aq_inner(parent)

def get_utility_for_context(iface, context):
    """
    does a getSite / setSite dance to get the utility in the given
    context since five.localsitemanager has a bug which makes using
    getUtility's context argument fail;
    see https://bugs.launchpad.net/zope2/+bug/223872
    """
    new_site = interface_in_aq_chain(context, ISite)
    orig_site = getSite()
    setSite(new_site)
    utility = getUtility(iface) # may raise an exception, this is okay
    setSite(orig_site)
    return utility

timestamp_cache = {}

def timestamp_memoize(secs):
    """
    Decorator to memoize the return value of the wrapped function for
    the specified number of seconds.  Stores the value in a global
    dict, keyed by the function's dotted name.
    """
    def arg_wrapper(fn):
        fn_key = fn.__name__
        fn_self = getattr(fn, '__self__', None)
        if fn_self is not None:
            # we're a method, get dotted name of the object's class
            klass = fn_self.__class__
            fn_key = '%s.%s.%s' % (klass.__module__, klass.__name__, fn_key)
        else:
            # we're a function, we can compute our own dotted name
            fn_key = '%s.%s' % (fn.__module__, fn_key)
        
        def wrapped(*arg, **kw):
            global timestamp_cache
            timestamp, value = timestamp_cache.get(fn_key, (0, None))
            now = time.time()
            if now - timestamp > secs:
                value = fn(*arg, **kw)
                timestamp_cache[fn_key] = (now, value)
            return value
        return wrapped

    return arg_wrapper


# XXX Temporary hack to allow semi-convenient usage of functions in
# templates, along the lines of Sputnik's SputnikUtils view.  A TALES
# namespace would be much cleaner; see comments in opencore.tales.utils 
# for problems with that. Once that works, this view should die.

from opencore.tales.utils import member_title
from Products.Five.browser import BrowserView

class OpencoreUtils(BrowserView):
    def member_title(self, arg):
        return member_title(arg)
    def topp_url(self):
        cfg = getUtility(IProvideSiteConfig)
        # XXX HARDCODED DOMAIN
        return cfg.get('topp_url', 'http://topp.openplans.org')
