from AccessControl.SecurityManagement import newSecurityManager
from Products.OpenPlans.Extensions.create_test_content import create_test_content
from Products.PloneTestCase.setup import portal_name
from Products.PloneTestCase.setup import portal_owner
from Testing import ZopeTestCase
from plone.memoize import view, instance
from zope.app.annotation.interfaces import IAnnotations
from zope.publisher.browser import TestRequest
from zope.testing.cleanup import cleanUp
from opencore.configuration.setuphandlers import Z_DEPS, DEPS


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

def clear_view_memo(request):
    anot = IAnnotations(request)
    if anot.has_key(view.ViewMemo.key):
        del anot[view.ViewMemo.key]

def clear_instance_memo(obj):
    instance._m.clear(obj)

def clear_all_memos(view):
    clear_instance_memo(view)
    clear_view_memo(view.request)


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
    from zope.app.component.interfaces import IPossibleSite, ISite
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
