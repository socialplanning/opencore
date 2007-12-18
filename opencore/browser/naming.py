"""
tools for working with naming

see: setup.txt and wiki/add.txt for usage
@@ separate out tests
"""
from opencore.browser.base import BaseView
from opencore.browser.formhandler import button, post_only, anon_only, octopus
from opencore.interfaces.browser import IIgnorableDummy 
from zExceptions import Redirect
from zope.app.apidoc.component import getRequiredAdapters as get_required
from zope.interface import providedBy
from zope.publisher.interfaces import IRequest
import itertools


class Dummy(BaseView):
    """Creates dummy for blocking the overcreation of a path (as
    determined by the zcml registration name).  Any view registered
    with this class will show up in `get_view_names`

    Redirects to the preferences view and is intend for use with projects."""
    def __init__(self, context, request):
        super(Dummy, self).__init__(context, request)
        
    def __call__(self, *args, **kw):
        raise Redirect, "%s/%s" %(self.area.absolute_url(), "preferences")

class IgnorableDummy(Dummy):
    """same as `Dummy` but the `ignorable` flag will filter these from
    a return by `get_view_names`.  Useful for preserving names for
    special persistent objects"""
    implements(IIgnorableDummy)

def get_view_names(obj, ignore_dummy=False):
    """Gets all view names for a particular object"""
    ifaces = providedBy(obj)
    regs = itertools.chain(*(get_required(iface, withViews=True) \
                             for iface in ifaces))
    if ignore_dummy:
        return set(reg.name for reg in regs\
               if reg.required[-1].isOrExtends(IRequest) and not IIgnorableDummy.providedBy(reg.value))
    return set(reg.name for reg in regs\
               if reg.required[-1].isOrExtends(IRequest))
