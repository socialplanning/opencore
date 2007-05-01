from Testing import ZopeTestCase
from AccessControl.SecurityManagement import newSecurityManager
from Products.PloneTestCase.setup import portal_name
from Products.PloneTestCase.setup import portal_owner
from Products.OpenPlans.Extensions.create_test_content import create_test_content

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
