import urllib
import hmac, sha
from httplib2 import Http
from opencore.wordpress.uri import get as uri_get

def send_to_wordpress(uri, username, params, context):
    """Send some data (params) to wordpress with the given user.
       The context is used to find the secret"""
    uri = '%s/%s' % (uri_get(), uri)
    acl_users = context.acl_users
    auth = acl_users.credentials_signed_cookie_auth
    secret = auth.secret

    sig = hmac.new(secret, username, sha).digest()
    params['signature'] = sig = sig.encode('base64').strip()
    params = urllib.urlencode(params)

    http = Http()
    response, content = http.request(uri, 'POST', headers={'Content-type': 'application/x-www-form-urlencoded'}, body=params)
    if response.status != 200:
        raise AssertionError('Failed to update wordpress: %s %s' % (response.status, content))

def notify_wordpress_user_created(mem, event):
    uri = "openplans-create-user.php"
    username = mem.getId()
    params = dict(
            username=username,
            email=mem.getEmail(),
            )
    send_to_wordpress(uri, username, params, mem)

def notify_wordpress_user_joined_project(mship, event):
    uri = "openplans-add-usertoblog.php"
    username = mship.getId()
    team = mship.aq_inner.aq_parent
    params = dict(
            username=username,
            project=team.getId(),
            role=team.getHighestTeamRoleForMember(username),
            )
    send_to_wordpress(uri, username, params, mship)

def notify_wordpress_email_changed(mem, event):
    uri = 'openplans-change-email.php'
    username = mem.getId()
    params = dict(
            username=username,
            email=mem.getEmail(),
            )
    send_to_wordpress(uri, username, params, mem)

def notify_wordpress_role_changed(mship, event):
    uri = 'openplans-change-role.php'
    username = mship.getId()
    team = mship.aq_inner.aq_parent
    proj_id = team.getId()
    params = dict(
            username=username,
            project=team.getId(),
            role=team.getHighestTeamRoleForMember(username),
            )
    send_to_wordpress(uri, username, params, mship)

def notify_wordress_user_left_project(mship, event):
    uri = 'openplans-remove-userfromblog.php'
    username = mship.getId()
    team = mship.aq_inner.aq_parent
    params = dict(
            username=username,
            project=team.getId(),
            )
    send_to_wordpress(uri, username, params, mship)
