##############################################################################
#
# Copyright (c) 2007 The Open Planning Project. All Rights
# Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Class: SignedCookieAuthHelper

$Id: SignedCookieAuthHelper.py 72211 2007-01-24 12:41:44Z novalis $
"""

from base64 import encodestring, decodestring
from urllib import quote, unquote

from AccessControl.SecurityInfo import ClassSecurityInfo
from OFS.Folder import Folder
from App.class_init import default__class_init__ as InitializeClass

from Products.PluggableAuthService.interfaces.plugins import \
    ILoginPasswordHostExtractionPlugin, IChallengePlugin, ICredentialsUpdatePlugin, \
    ICredentialsResetPlugin

from Products.PluggableAuthService.utils import classImplements

from Products.PluggableAuthService.plugins.CookieAuthHelper import ICookieAuthHelper
from Products.PlonePAS.plugins.cookie_handler import ExtendedCookieAuthHelper

import sha

from Acquisition import aq_base

def manage_addSignedCookieAuthHelper(self, id, title='',
                                       RESPONSE=None, **kw):
    """Create an instance of a extended cookie auth helper.
    """

    self = self.this()

    o = SignedCookieAuthHelper(id, title, **kw)
    self._setObject(o.getId(), o)
    o = getattr(aq_base(self), id)

    if RESPONSE is not None:
        RESPONSE.redirect('manage_workspace')

from Globals import DTMLFile
manage_addSignedCookieAuthHelperForm = DTMLFile("../zmi/SignedCookieAuthHelperForm", globals())


class SignedCookieAuthHelper(ExtendedCookieAuthHelper):
    """ Multi-plugin for managing details of Cookie Authentication with signing. """

    meta_type = 'Signed Cookie Auth Helper'
    security = ClassSecurityInfo()
    secret = 'secret'

    security.declarePrivate('extractCredentials')
    def extractCredentials(self, request):
        """ Extract credentials from cookie or 'request'. """
        creds = {}
        cookie = request.get(self.cookie_name, '')
        # Look in the request.form for the names coming from the login form
        login = request.form.get('__ac_name', '')

        if login and request.form.has_key('__ac_password'):
            creds['login'] = login
            creds['password'] = request.form.get('__ac_password', '')

        elif cookie and cookie != 'deleted':
            cookie_val = decodestring(unquote(cookie))
            login, password, hash = cookie_val.split(':')

            if not hash == sha.new(login + password + self.secret).hexdigest():
                return None

            creds['login'] = login
            creds['password'] = password

        if creds:
            creds['remote_host'] = request.get('REMOTE_HOST', '')

            try:
                creds['remote_address'] = request.getClientAddr()
            except AttributeError:
                creds['remote_address'] = request.get('REMOTE_ADDR', '')

        return creds

    security.declarePrivate('updateCredentials')
    def updateCredentials(self, request, response, login, new_password):
        """ Respond to change of credentials (NOOP for basic auth). """

        auth = sha.new(login + new_password + self.secret).hexdigest()
        cookie_val = encodestring('%s:%s:%s' % (login, new_password, auth))
        cookie_val = cookie_val.rstrip()
        response.setCookie(self.cookie_name, quote(cookie_val), path='/')


classImplements( SignedCookieAuthHelper
               , ICookieAuthHelper
               , ILoginPasswordHostExtractionPlugin
               , IChallengePlugin
               , ICredentialsUpdatePlugin
               , ICredentialsResetPlugin
               )

InitializeClass(SignedCookieAuthHelper)

