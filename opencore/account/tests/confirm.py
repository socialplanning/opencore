class stubbed_confirm(object):
    """
    ===============================
     account confirmation
    ==============================


    Confirmation
    ============

    Test the account confirmation view.

        >>> view = portal.restrictedTraverse("@@confirm-account")

    The view gets the confirmation key from the request form.

        >>> view.key
        ''
        >>> view.request.form['key'] = 'gadzooks'
        >>> view.key
        'gadzooks'

    The view's member will be None if the key is missing or invalid.  (We
    have to keep re-traversing the view because the member property is
    memoized.)

        >>> view = portal.restrictedTraverse("@@confirm-account")
        >>> view.request.form.clear()
        >>> print view.member
        None
        >>> view = portal.restrictedTraverse("@@confirm-account")
        >>> view.request.form['key'] = 'nonsense'
        >>> print view.member
        None

    The view's member will be a member object iff the key is a valid
    confirmation key. (See below in the integration test.)

    Confirming an unconfirmed member will succeed with no message::

        >>> test_member = StubMemberWorkflow('bob')
        >>> test_member.is_unconfirmed()
        True
        >>> view.confirm(test_member)
        True
        >>> test_member.is_unconfirmed()
        False
        >>> view.portal_status_message
        []

    Confirming an already-confirmed member will fail with an error
    message::

        >>> test_member.is_unconfirmed()
        False
        >>> view.confirm(test_member)
        False
        >>> view.portal_status_message   # XXX how do i get the az translation?
        [u'...not pending...']


    Calling handle_confirmation() when member is None should redirect you to
    the login page, and give you an error message::

        >>> view = portal.restrictedTraverse("@@confirm-account")
        >>> view.request.form.clear()
        >>> print view.member
        None
        >>> view.handle_confirmation()
        'http://nohost/plone/login'
        >>> get_status_messages(view)
        [u'Denied...']


    Now we want to test handle_confirmation with a stub member.
    Since the member is a property, this is a little awkward::

        >>> view = portal.restrictedTraverse("@@confirm-account")
        >>> clear_status_messages(view)
        >>> view.request.form.clear()
        >>> orig_member = view.__class__.member
        >>> view.__class__.member = StubMemberWorkflow('fred', confirmed=False)

    And we need to monkey-patch PAS so it doesn't complain about our
    stub member:

        >>> from Products.PluggableAuthService.PluggableAuthService import PluggableAuthService as PAS
        >>> PAS._orig_getUserById = PAS.getUserById
        >>> PAS.getUserById = stub_getUserById

    Calling handle_confirmation with an unconfirmed member should
    confirm you and redirect to the "initial login" welcome page::

        >>> IHandleMemberWorkflow(view.member).is_unconfirmed()
        True
        >>> view.handle_confirmation()
        'http://nohost/plone/init-login'
        >>> IHandleMemberWorkflow(view.member).is_unconfirmed()
        False
        >>> get_status_messages(view)
        []

    Calling handle_confirmation with a confirmed member should also
    redirect you to the login page, with an error status message::

        >>> IHandleMemberWorkflow(view.member).is_unconfirmed()
        False
        >>> view.handle_confirmation()
        'http://nohost/plone/login'
        >>> get_status_messages(view)
        [u'...not pending...']

    Now clean up the stub member and un-patch the monkey. The EPA fine for
    not doing this is $1M.

        >>> view.__class__.member = orig_member
        >>> view = portal.restrictedTraverse('@@confirm-account')
        >>> view.request.form.clear()
        >>> print view.member
        None
        >>> PAS.getUserById = PAS._orig_getUserById
        >>> del PAS._orig_getUserById


    """
    

def real_confirm():
    """
    Confirming a Real OpenMember
    ===============================

    First create a user and get their key.
    XXX we're not really testing this stuff, we just want a user to
    use for integration testing... real tests are in README.
    This sure is a huge pile o' stuff.

        >>> view = portal.restrictedTraverse("@@join")
        >>> self.logout()
        >>> request = view.request
        >>> request.environ["REQUEST_METHOD"] = "POST"
        >>> form = dict(id='foobar',
        ...             email='foobar@example.com',
        ...             password= 'testy',
        ...             confirm_password='testy')
        >>> request.form.update(form)
        >>> member = view.create_member()
        >>> from Products.CMFCore.utils import getToolByName
        >>> mt = getToolByName(portal, "portal_memberdata")
        >>> user = mt.restrictedTraverse('foobar')
        >>> self.loginAsPortalOwner()
        >>> getkey = user.restrictedTraverse("getUserConfirmationCode")
        >>> key = getkey()
        >>> self.logout()
        >>> clear_status_messages(view)

    Now we call the confirmation view.  Calling the view without the
    proper key will redirect to login with a message::

        >>> view = portal.restrictedTraverse("@@confirm-account")
        >>> view.request.form.clear()
        >>> view()
        'http://nohost/plone/login'
        >>> get_status_messages(view)
        [u'Denied...']


    And calling with the key will bring you to your initial login welcome page::

        >>> view = portal.restrictedTraverse("@@confirm-account")
        >>> view.request.form.clear()
        >>> view.request.form['key'] = key
        >>> view()
        'http://nohost/plone/init-login'
        >>> get_status_messages(view)
        []

    Calling again tells you you've already confirmed:

        >>> view = portal.restrictedTraverse("@@confirm-account")
        >>> view.request.form.clear()
        >>> clear_status_messages(view)
        >>> view.request.form['key'] = key
        >>> view()
        'http://nohost/plone/login'
        >>> get_status_messages(view)
        [u'...not pending...']



    Remove test_user_1_
    ===================

    Ensure test atomicity by removing the created user:

        >>> self.logout()
        >>> portal.portal_memberdata.manage_delObjects('test_user_1_')

    """
