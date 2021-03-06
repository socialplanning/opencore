from AccessControl.SecurityManagement import newSecurityManager
from Products.PloneTestCase.setup import portal_owner
from Products.PloneTestCase.setup import portal_name
from Testing import ZopeTestCase

from types import UnicodeType
from zope.publisher.browser import TestRequest
from zope.testing.cleanup import cleanUp
from opencore.configuration.setuphandlers import Z_DEPS, DEPS

from opencore.utils import clear_all_memos, clear_instance_memo, clear_view_memo #BBB

def get_view(context, view_class, request):
    """
    convenience function for directly instantiating
    a useable (acquisition-wrapped) view object

    http://www.coactivate.org/projects/opencore/lists/opencore-dev/archive/2009/05/1241281586467
    """
    view = view_class(context, request)
    view = view.__of__(context)
    return view

def login_portal_owner(app=None):
    if app is None:
        app = ZopeTestCase.app()
    user = app.acl_users.getUser(portal_owner)
    newSecurityManager(app, user)

def get_portal(app=None, portal_name=portal_name):
    if app is None:
        app = ZopeTestCase.app()
    return getattr(app, portal_name)

getPortal = get_portal


def get_portal_as_owner(app=None):
    if app is None:
        app = ZopeTestCase.app()
    login_portal_owner(app)
    return get_portal(app)


def makeContent(container, id, portal_type, **kw):
    """fx for making content in a container"""
    container.invokeFactory(id=id, type_name=portal_type, **kw)
    o = getattr(container, id)
    return o

def clear_status_messages(view):
    """Clear all portal status messages from cookies, the request,
    and the response. I hope.
    """
    from Products.statusmessages.interfaces import IStatusMessage
    request = view.request
    IStatusMessage(request).showStatusMessages()  # this clears cookies.
    for mapping in request.form, request.cookies, request.other:
        if mapping.has_key('portal_status_message'):
            del(mapping['portal_status_message'])

def get_status_messages(view):
    """Return (and clear) the view's status messages, regardless of
    redirect status. Sorted lexicographically.
    """
    restore = False
    if hasattr(view, '_redirected'):
        restore = True
        del view._redirected
    messages = view.portal_status_message
    if restore:
        view._redirected = True
    return sorted(messages)


class RESPONSE(object):
    
    def __init__(self):
        self.headers = dict()
        
    def redirect(self, url, lock=None):
        self.status=302
        self.headers['location']=url
        self.lock = lock


def new_request(**kwargs):
    request = TestRequest(form=kwargs)
    request.RESPONSE=RESPONSE()
    return request


def setDebugMode(mode):
    """
    Allows manual setting of Five's inspection of debug mode to allow for
    zcml to fail meaningfully
    """
    import Products.Five.fiveconfigure as fc
    fc.debug_mode = mode


def safe_load_site():
    """Load entire component architecture (w/ debug mode on)"""
    cleanUp()
    setDebugMode(1)
    import Products.Five.zcml as zcml
    zcml.load_site()
    setDebugMode(0)


def safe_load_site_wrapper(function):
    """Wrap function with a temporary loading of entire component architecture"""
    def wrapper(*args, **kw):
        safe_load_site()
        value = function(*args, **kw)
        cleanUp()
        import Products.Five.zcml as zcml
        zcml._initialized = 0
        return value
    return wrapper


def monkeyAppAsSite():
    # the python equivalent of load app as a localsite via zcml
    # import and call if you want to be able to treat the 
    import OFS.Application 
    from Products.Five.site.metaconfigure import classSiteHook
    from Products.Five.site.localsite import FiveSite

    from zope.interface import classImplements
    from zope.app.component.interfaces import IPossibleSite
    classSiteHook(OFS.Application.Application, FiveSite)
    classImplements(OFS.Application.Application, IPossibleSite)


def newuser():
    """ loads up an unrestricted security manager"""
    from AccessControl.SecurityManagement import newSecurityManager
    from AccessControl.User import UnrestrictedUser
    newSecurityManager( {}, UnrestrictedUser('debug', 'debug', [], [] ))

def zinstall_products():
    for product in Z_DEPS + DEPS:
        ZopeTestCase.installProduct(product)


def monkey_proj_noun(newname='project'):
    """temporarily switch the word we use for 'project' or 'group' or ..."""
    # XXX Need a better way to do this, it's horrible to patch an
    # ever-growing list of modules.  The function should be a utility
    # and we just swap out an implementation?
    from opencore.browser import base
    from opencore.project import utils
    from opencore.listen import events
    from Products.OpenPlans.content import project
    if not hasattr(utils, '_old_project_noun'):
        utils._old_project_noun = utils.project_noun
    project_noun = lambda: newname
    for module in (utils, base, events, project):
        module.project_noun = project_noun

def unmonkey_proj_noun():
    """temporarily switch the word we use for 'project' or 'group' or ..."""
    from opencore.browser import base
    from opencore.project import utils
    from opencore.listen import events
    from Products.OpenPlans.content import project
    if hasattr(utils, '_old_project_noun'):
        for module in (base, utils, events, project):
            module.project_noun = utils._old_project_noun
        del( utils._old_project_noun)
        
from Products.CMFPlone.patches.unicodehacks import FasterStringIO
from StringIO import StringIO
orig_fsio_write = FasterStringIO.write
orig_sio_write = StringIO.write

def monkey_stringio():
    """monkeypatch StringIO so it never fails w/ unicode errors"""
    def new_fsio_write(self, s):
        if isinstance(s, UnicodeType):
            s = s.encode('utf8', 'replace')
        return orig_fsio_write(self, s)
    FasterStringIO.write = new_fsio_write

    def new_sio_write(self, s):
        if isinstance(s, UnicodeType):
            s = s.encode('utf8', 'replace')
        return orig_sio_write(self, s)
    StringIO.write = new_sio_write

def unmonkey_stringio():
    FasterStringIO.write = orig_fsio_write
    StringIO.write = orig_sio_write
