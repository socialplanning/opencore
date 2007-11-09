from Testing import ZopeTestCase
from AccessControl.SecurityManagement import newSecurityManager
from Products.PloneTestCase.setup import portal_name
from Products.PloneTestCase.setup import portal_owner
from Products.OpenPlans.Extensions.create_test_content import create_test_content
from zope.app.annotation.interfaces import IAnnotations
from plone.memoize import view, instance
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

def zinstall_products():
    for product in Z_DEPS + DEPS:
        ZopeTestCase.installProduct(product)
