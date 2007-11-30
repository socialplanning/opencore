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
    return zutils.aq_iface(viewlet.context, viewlet.container)

def nofilter(viewlet):
    return True

def contained_item_url(viewlet):
    item = contained_within(viewlet)
    if item is None:
        url = viewlet.context.absolute_url()
    else:
        url = item.absolute_url()
    return '%s/%s' % (url, viewlet.item_url)

def portal_and_item_url(viewlet):
    portal = getToolByName(viewlet.context, 'portal_url').getPortalObject()
    return '%s/%s' % (portal.absolute_url(), viewlet.item_url)

def people_url(viewlet):
    portal = getToolByName(viewlet.context, 'portal_url').getPortalObject()
    return '%s/people' % portal.absolute_url()

def projects_url(viewlet):
    portal = getToolByName(viewlet.context, 'portal_url').getPortalObject()
    return '%s/projects' % portal.absolute_url()

def project_create_url(viewlet):
    portal = getToolByName(viewlet.context, 'portal_url').getPortalObject()
    return '%s/projects/create' % portal.absolute_url()

def member_wiki_url(viewlet):
    mstool = getToolByName(viewlet.context, 'portal_membership')
    home_folder = mstool.getHomeFolder()
    id_ = home_folder.getId()
    return '%s/%s-home' % (home_folder.absolute_url(), id_)

def project_wiki_url(viewlet):
    proj = contained_within(viewlet)
    return '%s/project-home' % proj.absolute_url()

def if_request_starts_with_url(viewlet):
    return viewlet.request.ACTUAL_URL.startswith(viewlet.url())

def if_portal_people_or_projects(viewlet):
    context = viewlet.context
    for iface in IPloneSiteRoot, IAddProject, IAmAPeopleFolder:
        if iface.providedBy(context):
            return True
    return False

def if_projects_selected(viewlet):
    return (IAddProject.providedBy(viewlet.context)
            and not viewlet.context.request.ACTUAL_URL.endswith('/create'))

def openpage_provided(viewlet):
    return IOpenPage.providedBy(viewlet.context)

def default_css(viewlet):
    return viewlet.selected() and 'oc-topnav-selected' or None

def join_css(viewlet):
    return viewlet.selected() and 'oc-topnav-selected' or 'oc-topnav-join'

def not_part_of_project(viewlet):
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
