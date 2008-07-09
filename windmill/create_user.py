from utils import base_url
from utils import get_auth_portal
from utils import zope_delobject

username = u'testuser'
password = u'testy'
fullname = u'Test User'
email = u'test@example.com'

def create_user(client, username=username, password=password,
                fullname=fullname, email=email):
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
    client.waits.forPageLoad()
    client.asserts.assertNode(id=u'oc-deadend-message-container')
    client.asserts.assertNode(xpath=u'/html/body/div/div/div/div/div')
    #client.asserts.assertText(xpath=u'/html/body/div/div/div/div/div',
    #                          validator=u'Thanks for joining OpenPlans, %s!' % username)
        
    portal = get_auth_portal()
    confirmation_code = getattr(portal.portal_memberdata,
                                username).getUserConfirmationCode()

    client.open(url="%s/confirm-account?key=%s" % (base_url,
                                                   confirmation_code))
    client.waits.forPageLoad()
    client.asserts.assertNode(xpath=u'/html/body/div/div/div/div/div/div/h1')
    client.asserts.assertText(xpath=u'/html/body/div/div/div/div/div/div/h1',
                              validator=u'Welcome to OpenPlans!')
    client.asserts.assertNode(link=u'Complete your profile')
    client.asserts.assertNode(id=u'ext-gen17')
    client.asserts.assertText(id=u'ext-gen17', validator=username)
    client.asserts.assertNode(link=u'Sign out')

def create_user_cleanup(username=username):
    """
    Clean up after the create_user test.
    """
    # should automatically trigger homepage deletion
    zope_delobject('portal_memberdata', username)
