import urllib
import hmac, sha

from decorator import decorator

from zope.component import getUtility

from Products.CMFCore.utils import getToolByName

from opencore.utility.interfaces import IHTTPClient
from opencore.wordpress.uri import get as uri_get
from opencore.project.utils import get_featurelets

@decorator
def project_contains_blog(f, mship_obj, event):
    """decorator to verify that the project has a blog before
       sending the event to wordpress"""
    team = mship_obj.aq_inner.aq_parent
    proj_id = team.getId()
    portal = getToolByName(mship_obj, 'portal_url').getPortalObject()
    try:
        project = portal.projects._getOb(proj_id)
    except KeyError:
        # cannot find project with same name as team (unit test only?)
        return
    for flet in get_featurelets(project):
        if flet['name'] == 'blog':
            break
    else:
        # no blog on project
        return
    f(mship_obj, event)

def send_to_wordpress(uri, username, params, context):
    """Send some data (params) to wordpress with the given user.
       The context is used to find the secret"""
    uri = '%s/%s' % (uri_get(), uri)
    acl_users = context.acl_users
    auth = acl_users.credentials_signed_cookie_auth
    secret = auth.secret

    sig = hmac.new(secret, username, sha).digest()
    params['signature'] = sig = sig.encode('base64').strip()
    project = params.get('domain', None)
    if project is not None:
        params['domain'] = '%s.openplans.org' % project
    params = urllib.urlencode(params)

    http = getUtility(IHTTPClient)
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

@project_contains_blog
def notify_wordpress_user_joined_project(mship, event):
    uri = "openplans-add-usertoblog.php"
    username = mship.getId()
    team = mship.aq_inner.aq_parent
    params = dict(
            username=username,
            domain=team.getId(),
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

@project_contains_blog
def notify_wordpress_role_changed(mship, event):
    uri = 'openplans-change-role.php'
    username = mship.getId()
    team = mship.aq_inner.aq_parent
    proj_id = team.getId()
    params = dict(
            username=username,
            domain=team.getId(),
            role=team.getHighestTeamRoleForMember(username),
            )
    send_to_wordpress(uri, username, params, mship)

@project_contains_blog
def notify_wordress_user_left_project(mship, event):
    uri = 'openplans-remove-userfromblog.php'
    username = mship.getId()
    team = mship.aq_inner.aq_parent
    params = dict(
            username=username,
            domain=team.getId(),
            )
    send_to_wordpress(uri, username, params, mship)
