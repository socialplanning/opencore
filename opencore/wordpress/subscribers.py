from Products.CMFCore.utils import getToolByName
from decorator import decorator
from opencore.interfaces import IProject
from opencore.project.utils import get_featurelets
from opencore.utility.interfaces import IHTTPClient
from opencore.utility.interfaces import IProvideSiteConfig
from zope.component import getUtility
import hmac, sha
import urllib
import logging

log = logging.getLogger('opencore.wordpress')

@decorator
def project_contains_blog(f, obj, event):
    """decorator to verify that the project has a blog before
       sending the event to wordpress"""
    if IProject.providedBy(obj):
        proj_id = obj.getId()
        project = obj
    else:
        # it's a membership object
        team = obj.aq_inner.aq_parent
        proj_id = team.getId()
        portal = getToolByName(obj, 'portal_url').getPortalObject()
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
    f(obj, event)

def try_to_send_to_wordpress(uri, username, params, context):
    """Send some data (params) to wordpress with the given user.
       The context is used to find the secret.  If this fails,
       return the error"""
    wp_uri = getUtility(IProvideSiteConfig).get('wordpress uri')
    if not wp_uri:
        # either None or empty value mean do nothing
        log.info('Failed to connect to WordPress: no WP URI set')
        return 200, 'Failed to connect to WordPress: no WP URI set'
        
    uri = '%s/%s' % (wp_uri, uri)
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
    headers={'Content-type': 'application/x-www-form-urlencoded'}
    response, content = http.request(uri, 'POST', headers=headers,
                                     body=params)

    return response.status, content

def send_to_wordpress(uri, username, params, context):
    """Send some data to wordpress with the given user.  Assume that this
    is going to work, and raise an assertion if it does not."""
    error_code, error_message = try_to_send_to_wordpress(uri, username, params, context)
    if error_code != 200:
        raise AssertionError('Failed to update wordpress: %s %s' % (error_code, error_message))

def notify_wordpress_user_created(mem, event):
    ftool = getToolByName(mem, 'portal_factory')
    if ftool.isTemporary(mem):
        # don't create records for the temporary member objects
        return
    uri = "openplans-create-user.php"
    #XXX we can't get the member home folder by calling
    # mship_tool.getHomeFolder because it hasn't been created yet
    username = mem.getId()
    portal_url = getToolByName(mem, 'portal_url')()
    profile_page = 'profile'
    home_page = '%s/people/%s/%s' % (portal_url, username, profile_page)
    email=mem.getEmail()
    if not email:
        # get email from request form... not ideal to use acquisition
        # to get the request, but not sure how else to get it (ra)
        request = mem.REQUEST
        email = request.form.get('email', '')
    params = dict(
            username=username,
            email=email,
            home_page=home_page,
            )
    error_code, error_message = try_to_send_to_wordpress(uri, username, params, mem)
    if error_code == 400 and error_message == ("User with name %s already exists!" % username):
        return
    elif error_code != 200:
        raise AssertionError('Failed to update wordpress: %s %s' % (error_code, error_message))

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

def notify_wordress_user_removed(mem, event):
    uri = 'openplans-remove-user.php'
    username = mem.getId()
    params = dict(
            username=username,
            )
    send_to_wordpress(uri, username, params, mem)

def notify_wordpress_user_modified(mem, event):
    old_id = getattr(event, '_old_id', None)
    # are we changing the user login?
    if old_id is not None:
        # yup.  remove the old record.
        uri = 'openplans-remove-user.php'
        params = dict(username=old_id)
        send_to_wordpress(uri, old_id, params, mem)
        # and create the new one.
        notify_wordpress_user_created(mem, event)
    else:
        uri = 'openplans-user-modified.php'
        username = mem.getId()
        params = dict(
            username=username,
            email=mem.getEmail(),
            display_name=mem.Title(),
            )
        send_to_wordpress(uri, username, params, mem)

@project_contains_blog
def notify_wordpress_project_deleted(project, event):
    uri = 'openplans-delete-blog.php'
    params = dict(
        # XXX this hardcoded 'openplans.org' stuff has got to go :(
        domain=project.getId(),
        )
    mtool = getToolByName(project, 'portal_membership')
    mem = mtool.getAuthenticatedMember()
    username = mem.getId()
    try: 
        send_to_wordpress(uri, username, params, project)
    except AssertionError, e:
        # we're deleting the project; we don't care if there's no matching blog
        if not 'already been deleted' in str(e):
            raise

