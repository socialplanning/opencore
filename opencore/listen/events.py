from decorator import decorator

from zope.component import getUtility
from zope.app.event.objectevent import ObjectCreatedEvent
from zope.event import notify

from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IWriteMembershipList
from Products.listen.interfaces import IListLookup
from opencore.i18n import _
from opencore.listen.mailinglist import OpenMailingList
from opencore.project.utils import get_featurelets
from utils import getSuffix
from opencore.project.utils import project_noun 
from zope.i18n import translate

# make sure that modification date gets updated
# when new messages are sent to list
def mailinglist_msg_delivered(ml, event):
    ml.setModificationDate()

from opencore.listen.interfaces import IListenFeatureletInstalled

def project_for_membership(mship):
    """
    This should really be IOpenProject(mship)...?
    """
    team = mship.aq_inner.aq_parent
    proj_id = team.getId()
    portal = getToolByName(mship, 'portal_url').getPortalObject()
    return portal.projects[proj_id]

def member_joined_project(mship, event):
    project = project_for_membership(mship)
    default_list_name = '%s-discussion' % project.getId()
    # \  / or just try: IListenContainer(project)[default_list_name]
    #  \/  ... which could be formalized to IListenContainer(project).default_list
    #      ..... so this whole function could look like:
    #      .....  IWriteMembershipList(IListenContainer(IOpenProject(mship)).default_list).subscribe(IOpenMember(mship))
    #      ..... if we really wanted it to
    if IListenFeatureletInstalled.providedBy(project):
        try:
            ml = project['lists'][default_list_name]
        except AttributeError:
            return
        memlist = IWriteMembershipList(ml)
        memlist.subscribe(mship.getId())

def member_left_project(mship, event):
    project = project_for_membership(mship)
    default_list_name = '%s-discussion' % project.getId()
    if IListenFeatureletInstalled.providedBy(project):
        try:
            ml = project['lists'][default_list_name]
        except AttributeError:
            return
        memlist = IWriteMembershipList(ml)
        memlist.unsubscribe(mship.getId())

def listen_featurelet_installed(proj, event):
    """need to create a default discussion mailing list
       and subscribe all project members to the list"""
    proj_id = proj.getId()
    proj_title = proj.Title().decode('utf-8')
    ml_id = '%s-discussion' % proj_id
    address = '%s%s' % (ml_id, getSuffix())

    # need to verify that a mailing list with this name isn't already created
    portal = getToolByName(proj, 'portal_url').getPortalObject()
    ll = getUtility(IListLookup, context=portal)
    if ll.getListForAddress(address) is not None:
        # XXX we'll just silently fail for now, not sure what else we can do
        # psm maybe?
        return

    # XXX we need a request utility
    request = proj.REQUEST
    # invokeFactory depends on the title being set in the request
    ml_title = u'%s discussion' % (proj_title)
    request.set('title', ml_title)
    lists_folder = proj.lists.aq_inner
    lists_folder.invokeFactory(OpenMailingList.portal_type, ml_id)
    ml = lists_folder._getOb(ml_id)
    ml.mailto = ml_id
    ms_tool = getToolByName(proj, 'portal_membership')
    cur_mem_id = unicode(ms_tool.getAuthenticatedMember().getId())
    ml.managers = (cur_mem_id,)
    ml.setDescription(translate(_(u'discussion_list_desc', u'Discussion list for this ${project_noun}, consisting of all ${project_noun} members.',
                                  mapping={'project_noun':project_noun()}),
                                            context=request))
    notify(ObjectCreatedEvent(ml))

    memlist = IWriteMembershipList(ml)

    cat = getToolByName(portal, 'portal_catalog')
    teams = getToolByName(portal, 'portal_teams')
    try:
        team = teams._getOb(proj_id)
    except KeyError:
        # if the team doesn't exist
        # then nobody is on the project yet
        # so we only need to subscribe the current user
        memlist.subscribe(cur_mem_id)
        return
    active_states = teams.getDefaultActiveStates()
    team_path = '/'.join(team.getPhysicalPath())
    mships = cat(portal_type='OpenMembership', review_state=active_states, path=team_path)
    for mship in mships:
        memlist.subscribe(mship.getId)
