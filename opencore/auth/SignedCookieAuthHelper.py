##############################################################################
#
# Copyright (c) 2007 The Open Planning Project. 
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the 
# Free Software Foundation, Inc., 
# 51 Franklin Street, Fifth Floor, 
# Boston, MA  02110-1301
# USA
#
##############################################################################
""" Class: SignedCookieAuthHelper

$Id: SignedCookieAuthHelper.py 72211 2007-01-24 12:41:44Z novalis $
"""

from base64 import encodestring, decodestring
from urllib import quote, unquote

import hmac
import sha
import os

from zope.interface import implements

from App import config

from Acquisition import aq_base

from AccessControl.SecurityInfo import ClassSecurityInfo
from OFS.Folder import Folder
from App.class_init import default__class_init__ as InitializeClass

from Products.PluggableAuthService.interfaces.plugins import \
    ILoginPasswordHostExtractionPlugin, IChallengePlugin, ICredentialsUpdatePlugin, \
    ICredentialsResetPlugin, IAuthenticationPlugin

from Products.PluggableAuthService.plugins.CookieAuthHelper import ICookieAuthHelper
from Products.PlonePAS.plugins.cookie_handler import ExtendedCookieAuthHelper

def getCookieDomainKW(context):
    domain_kw = {}
    app = context.getPhysicalRoot()
    bid_mgr = app._getOb('browser_id_manager', None)
    if bid_mgr is not None:
        domain = bid_mgr.getCookieDomain()
        if domain:
            domain_kw['domain'] = domain
    return domain_kw

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

from opencore.configuration import utils as conf_utils 

def get_secret_file_name():
    filename = conf_utils.product_config('topp_secret_filename', 'opencore.auth')
    if filename:
        return filename
    return os.path.join(os.environ.get('INSTANCE_HOME'), 'secret.txt')

def get_secret():
    secret_file_name = get_secret_file_name()

    if os.path.exists(secret_file_name):
        f = open(secret_file_name)
        password = f.readline().strip()
        f.close()
    else:
        #this may throw an error if the file cannot be created, but that's OK, because 
        #then users will know to create it themselves
        f = open(secret_file_name, "w")
        from random import SystemRandom
        random = SystemRandom()
        letters = [chr(ord('A') + i) for i in xrange(26)]
        letters += [chr(ord('a') + i) for i in xrange(26)]
        letters += map(str, xrange(10))
        password = "".join([random.choice(letters) for i in xrange(10)])
        f.write(password)
        f.close()
    return password

class SignedCookieAuthHelper(ExtendedCookieAuthHelper):
    """ Multi-plugin for managing details of Cookie Authentication with signing. """

    meta_type = 'Signed Cookie Auth Helper'
    security = ClassSecurityInfo()
    secret = get_secret()


    implements( ICookieAuthHelper
               , ILoginPasswordHostExtractionPlugin
               , IChallengePlugin
               , ICredentialsUpdatePlugin
               , ICredentialsResetPlugin
               , IAuthenticationPlugin )

    def generateHash(self, login):
        return hmac.new(self.secret, login, sha).hexdigest()

    def generateCookieVal(self, login):
        encoded = encodestring("%s\0%s" % (login, self.generateHash(login)))
        return quote(encoded.rstrip())

    def generateCookie(self, login):
        cookie_val = self.generateCookieVal(login)
        return '%s="%s"' % (self.cookie_name, cookie_val)

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
            login, hash = cookie_val.split('\0')

            if not hash == self.generateHash(login):
                return None

            creds['login'] = login
            #creds['password'] = password
            creds['hash'] = hash

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
        cookie_val = self.generateCookieVal(login)

        if request.get("no_expire_cookie"):
            response.setCookie(self.cookie_name, cookie_val, path='/',
                               expires="Sat, 06-May-2017 19:06:00 GMT")
        else:
            response.setCookie(self.cookie_name, cookie_val, path='/')

        domain_kw = getCookieDomainKW(self)
        if domain_kw:
            # can't use 'setCookie' again b/c it will slam the first value
            domain_cookie_value = '%s="%s"; Path=/; Domain=%s' % \
                (self.cookie_name, cookie_val,
                 domain_kw['domain'])
            if request.get("no_expire_cookie"):
                domain_cookie_value += "; Expires=Sat, 06-May-2017 19:06:00 GMT"
            response.addHeader('Set-Cookie', domain_cookie_value)
            
    security.declarePrivate('resetCredentials')
    def resetCredentials(self, request, response):
        """ clear cookie """
        response.expireCookie(self.cookie_name, path='/')
        domain_kw = getCookieDomainKW(self)
        if domain_kw:
            # can't use 'expireCookie' again b/c it will override
            exp_string = "Expires=Wed, 31-Dec-97 23:59:59 GMT; Max-Age=0"
            domain_cookie_expire = '%s="deleted"; Path=/; Domain=%s; %s' % \
                                   (self.cookie_name, domain_kw['domain'],
                                    exp_string)
            response.addHeader('Set-Cookie', domain_cookie_expire)

    #IAuthenticationPlugin

    def authenticateCredentials(self, credentials):
        login = credentials.get('login')
        cookiehash = credentials.get('hash')
        if cookiehash is not None and \
               cookiehash  == self.generateHash(login):
            # block remote auth
            credentials['opencore_auth_match'] = True
            return (login, login)

InitializeClass(SignedCookieAuthHelper)
