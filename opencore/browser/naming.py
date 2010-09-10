"""
tools for working with naming

see: setup.txt and wiki/add.txt for usage
@@ separate out tests
"""
from opencore.browser.base import BaseView
from zExceptions import Redirect
#from zope.app.apidoc.component import getRequiredAdapters as get_required
from zope.interface import providedBy
from zope.publisher.interfaces import IRequest
import itertools


class ProjectDummy(BaseView):
    """This is a dummy view used to take the place of a URL space that is not
    handled by Zope, or is configurable on an object.  When featurelets are
    available on projects, this prevents the creation of, for example, wiki
    pages that would be installed at this URL.  Views set up using this class
    will show up in the list of views associated with this object (which can be
    retrieved by using get_view_names).

    This implementation redirects back to the preferences page and is intended for use
    with projects."""
    def __init__(self, context, request):
        super(ProjectDummy, self).__init__(context, request)
        
    def __call__(self, *args, **kw):
        raise Redirect, "%s/%s" %(self.context.absolute_url(), "preferences")

class IgnorableProjectDummy(ProjectDummy):
    """same as `ProjectDummy` but the `ignorable` flag will filter these from
    a return by `get_view_names`.  Useful for preserving names for
    special persistent objects"""
    _dummy_ignore = True


def get_view_names(obj, ignore_dummy=False):
    """Gets all view names for a particular object"""
    ifaces = providedBy(obj)
    required = [] #(get_required(iface, withViews=True) for iface in ifaces)
    regs = itertools.chain(*required)

    if ignore_dummy:
        return set(reg.name for reg in regs \
                   if reg.required[-1].isOrExtends(IRequest) \
                   and not getattr(reg.value, '_dummy_ignore', False))
    
    return set(reg.name for reg in regs\
               if reg.required[-1].isOrExtends(IRequest))
