import urllib
import hmac, sha
from opencore.wordpress.uri import get as uri_get

def notify_wordpress_user_created(mem, event):
    uri = "%s/openplans-create-user.php" % uri_get()
    params = {}
    
    params['username'] = username = mem.id
    params['email'] = mem.getEmail()
    
    auth = mem.acl_users.credentials_signed_cookie_auth
    secret = auth.secret
    sig = hmac.new(secret, username, sha).digest()
    params['signature'] = sig = sig.encode('base64').strip()
    params = urllib.urlencode(params)

    response = urllib.urlopen(uri, params)
    response = response.read()
    if not response.startswith("Creating user"):
        raise AssertionError("Failed to update wordpress with newly created user. %s" % response)
