import urllib
import hmac, sha
from opencore.wordpress.uri import get as uri_get

def send_to_wordpress(uri, username, params, context, response_pred):
    """Send some data (params) to wordpress with the given user.
       The context is used to find the secret"""
    uri = '%s/%s' % (uri_get(), uri)
    acl_users = context.acl_users
    auth = acl_users.credentials_signed_cookie_auth
    secret = auth.secret

    sig = hmac.new(secret, username, sha).digest()
    params['signature'] = sig = sig.encode('base64').strip()
    params = urllib.urlencode(params)

    response = urllib.urlopen(uri, params)
    response = response.read()
    if not response_pred(response):
        raise AssertionError('Failed to update wordpress. %s' % response)

def must_start_with(good_response):
    """create a predicate function that determines
       if arg starts with good_response"""
    def response_pred(response_string):
        return response_string.startswith(good_response)
    return response_pred

def notify_wordpress_user_created(mem, event):
    uri = "openplans-create-user.php"
    username = mem.getId()
    params = dict(
            username=username,
            email=mem.getEmail(),
            )
    good_response = 'Creating user'
    send_to_wordpress(uri, username, params, mem, must_start_with(good_response))

def notify_wordpress_user_joined_project(mship, event):
    uri = "openplans-add-usertoblog.php"
    username = mship.getId()
    team = mship.aq_inner.aq_parent
    params = dict(
            username=username,
            project=team.getId(),
            role=team.getHighestTeamRoleForMember(username),
            )
    good_response = 'good message goes in here'
    send_to_wordpress(uri, username, params, mship, must_start_with(good_response))

def notify_wordpress_email_changed(mem, event):
    uri = 'openplans-change-email.php'
    username = mem.getId()
    params = dict(
            username=username,
            email=mem.getEmail(),
            )
    good_response = 'good message goes in here'
    response = send_to_wordpress(uri, username, params, mem, must_start_with(good_response))

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
    good_response = 'good message goes in here'
    response = send_to_wordpress(uri, username, params, mship, must_start_with(good_response))

def notify_wordress_user_left_project(mship, event):
    uri = 'openplans-remove-userfromblog.php'
    username = mship.getId()
    team = mship.aq_inner.aq_parent
    params = dict(
            username=username,
            project=team.getId(),
            )
    good_response = 'good message goes in here'
    response = send_to_wordpress(uri, username, params, mship, must_start_with(good_response))
