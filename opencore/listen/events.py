from decorator import decorator

from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IWriteMembershipList
from opencore.listen.mailinglist import addOpenMailingList
from opencore.project.utils import get_featurelets

# make sure that modification date gets updated
# when new messages are sent to list
def mailinglist_changed(ml, event):
    ml.setModificationDate()

#XXX this is directly copied from the wordpress event code to check
# need to extract a method, or utility, or something
@decorator
def listen_featurelet_installed(f, mship_obj, action):
    team = mship_obj.aq_inner.aq_parent
    proj_id = team.getId()
    portal = getToolByName(mship_obj, 'portal_url').getPortalObject()
    try:
        project = portal.projects._getOb(proj_id)
    except KeyError:
        # cannot find project with same name as team (unit test only?)
        return
    for flet in get_featurelets(project):
        if flet['name'] == 'listen':
            break
    else:
        # no mailing lists on project
        return
    f(mship_obj, action)


#XXX events handlers below are called for all lists
# maybe we should only do this for experimental projects first

@listen_featurelet_installed
def perform_listen_action(mship, action):
    mem_id = mship.getId()
    team = mship.aq_inner.aq_parent
    proj_id = team.getId()
    portal = getToolByName(mship, 'portal_url').getPortalObject()
    default_list_name = '%s-discussion' % proj_id
    try:
        ml = portal.projects._getOb(proj_id).lists._getOb(default_list_name)
    except AttributeError:
        print "no default project discussion list for '%s'" % proj_id
        return
    memlist = IWriteMembershipList(ml)
    getattr(memlist, action)(mem_id)

def member_joined_project(mship, event):
    perform_listen_action(mship, 'subscribe')

def member_left_project(mship, event):
    perform_listen_action(mship, 'unsubscribe')

def listen_featurelet_installed(proj, event):
    """need to create a default discussion mailing list
       and subscribe all project members to the list"""
    proj_id = proj.getId()
    proj_title = proj.Title()
    ml_id = '%s-discussion' % proj_id
    ml_title = u'%s discussion' % (proj_title)
    lists_folder = proj.lists
    addOpenMailingList(lists_folder, ml_id, ml_title)
    ml = lists_folder._getOb(ml_id)
    memlist = IWriteMembershipList(ml)

    portal = getToolByName(proj, 'portal_url').getPortalObject()
    cat = getToolByName(portal, 'portal_catalog')
    teams = getToolByName(portal, 'portal_teams')
    try:
        team = teams._getOb(proj_id)
    except KeyError:
        # if the team doesn't exist
        # then nobody is on the project yet
        # so we only need to subscribe the current user
        mship_tool = getToolByName(portal, 'portal_membership')
        mem_id = mship_tool.getAuthenticatedMember().getId()
        memlist.subscribe(mem_id)
        return
    active_state = teams.getDefaultActiveStates()
    team_url = team.absolute_url_path()
    mships = cat(portal_type='OpenMembership', review_state=active_states)
    for mship in mships:
        memlist.subscribe(mship.getId())
