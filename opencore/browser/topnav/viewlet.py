from opencore.interfaces import IOpenPage
from opencore.interfaces.adding import IAddProject
from opencore.interfaces.adding import IAmAPeopleFolder
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from topp.utils import zutils

# all viewlet methods used for the menuitem registration
# can be found below
# these control the various permutations required
# for displaying all menu items

def contained_within(viewlet):
    """walk up the acquisition chain and verify if the any either the context
       of the viewlet, or any of its parents provide the viewlet.container
       interface"""
    return zutils.aq_iface(viewlet.context, viewlet.container)

def nofilter(viewlet):
    """dummy function to always include a particular viewlet"""
    return True

def contained_item_url(viewlet):
    """return the viewlet's item_url relative to the viewlet.container's
       absolute url"""
    item = contained_within(viewlet)
    if item is None:
        url = viewlet.context.absolute_url()
    else:
        url = item.absolute_url()
    return '%s/%s' % (url, viewlet.item_url)

def people_url(viewlet):
    """return url of the people folder"""
    portal = getToolByName(viewlet.context, 'portal_url').getPortalObject()
    return '%s/people' % portal.absolute_url()

def projects_url(viewlet):
    """return url of the projects folder"""
    portal = getToolByName(viewlet.context, 'portal_url').getPortalObject()
    return '%s/projects' % portal.absolute_url()

def project_create_url(viewlet):
    """return the url of the project creation page"""
    portal = getToolByName(viewlet.context, 'portal_url').getPortalObject()
    return '%s/projects/create' % portal.absolute_url()

def member_wiki_url(viewlet):
    """return the url to the viewed user's wiki home page"""
    mf = contained_within(viewlet)
    return '%s/%s-home' % (mf.absolute_url(), mf.getId())

def project_wiki_url(viewlet):
    """return the url to the project's wiki home page"""
    proj = contained_within(viewlet)
    return '%s/project-home' % proj.absolute_url()

def if_request_starts_with_url(viewlet):
    """return true if the requested url starts with the particular viewlet's
       absolute url
       this handles most cases to see if a particular button should be
       selected"""
    return viewlet.request.ACTUAL_URL.startswith(viewlet.url())

def portal_people_or_projects(viewlet):
    """a particular set of viewlets get rendered when viewing the
       portal, people folder, or projects folder"""
    context = viewlet.context
    for iface in IPloneSiteRoot, IAddProject, IAmAPeopleFolder:
        if iface.providedBy(context):
            return True
    return False

def if_projects_selected(viewlet):
    """if we don't check that the viewed url ends with create, then the
       projects folder will be displayed as well (also in projects folder)"""
    return (IAddProject.providedBy(viewlet.context)
            and not viewlet.context.request.ACTUAL_URL.endswith('/create'))

def openpage_provided(viewlet):
    """return True if the viewlet context is a wiki page"""
    return IOpenPage.providedBy(viewlet.context)

def default_css(viewlet):
    """menu items have a special class if they are selected
       otherwise they have no class"""
    return viewlet.selected() and 'oc-topnav-selected' or None

def join_css(viewlet):
    """the join button is unique because it always has a class applied
       the difference is whether the current page is the join page or not"""
    return viewlet.selected() and 'oc-topnav-selected' or 'oc-topnav-join'

def not_part_of_project(viewlet):
    """return true if:
       1. the viewlet is in the context of a project
       2. the user is not a part of the project, or has not logged in"""
    proj = contained_within(viewlet)
    if proj is None:
        return False
    mstool = getToolByName(viewlet.context, 'portal_membership')
    if mstool.isAnonymousUser():
        return True
    mem = mstool.getAuthenticatedMember()
    team = proj.getTeams()[0]
    filter_states = tuple(team.getActiveStates()) + ('pending',)
    if mem.getId() in team.getMemberIdsByStates(filter_states):
        return False
    return True

def team_selected(viewlet):
    return (viewlet.context.request.ACTUAL_URL.endswith('/team') or
            viewlet.context.request.ACTUAL_URL.endswith('/manage-team'))
