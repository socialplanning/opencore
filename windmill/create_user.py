from functest import registry
from utils import get_admin_info
from xmlrpclib import Server

import urllib

def create_user(client, username=u'testuser', password=u'testy',
                fullname=u'Test User', email=u'test@example.com'):
    """
    Fills out the join form, retrieves confirmation key and finalizes
    registration.
    """
    client.click(link=u'Create account')
    client.waits.forPageLoad()
    client.type(text=username, id=u'id')
    client.type(text=fullname, id=u'fullname')
    client.type(text=email, id=u'email')
    client.type(text=password, id=u'password')
    client.type(text=password, id=u'confirm_password')
    client.click(name=u'task|join')
    return

    admin_uid, admin_pwd = get_admin_info()
    base_url = registry['url']
    scheme, uri = urllib.splittype(base_url) 
    host, path = urllib.splithost(uri)
    auth_url = "%s://%s:%s@%s%s/" % (scheme, admin_uid, admin_pwd, host, path)
    portal = Server(auth_url)
    confirmation_code = getattr(portal.portal_memberdata,
                                username).getUserConfirmationCode()

    client.open(url="%s/confirm-account?key=%s" % (base_url,
                                                   confirmation_code))
