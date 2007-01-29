from zope.component import queryMultiAdapter
from zope.component import getUtility

from Products.CMFCore.utils import getToolByName
from Products.Five.viewlet.viewlet import ViewletBase
from Products.OpenPlans.interfaces import IProject
from topp.featurelets.interfaces import IFeatureletSupporter
from projectinfo import ProjectInfoView
from memberinfo import MemberInfoView
from menu_item import MenuItem

class MenuItemList(ViewletBase):

    def __init__(self, context, request, view, manager):
        super(ViewletBase, self).__init__(context, request, view, manager)
        self._context = (context,)
        self.menu_items = []
        self.mtool = getToolByName(self.context, 'portal_membership')

    def menuItems(self):
        """ override this function """
        return self.menu_items

    def addMenuItem(self, title='', url=''):
        self.menu_items.append({'title': title, 'url': url})


class NavMenu(MenuItemList):
    ### different modes for the Navigation Secion of the Personal bar

    def addPersonalView(self):
        homefolder = self.mtool.getHomeFolder()
        member = self.mtool.getAuthenticatedMember()
        self.addMenuItem('my profile', homefolder.absolute_url())
        self.addMenuItem('my preferences', member.absolute_url() + '/edit')

    def addMemberView(self):
        memberfolder = self.memberInfoView.member_folder or self.mtool.getHomeFolder(self.memberInfoView.member.getId())
        if memberfolder:
            self.addMenuItem('member profile', memberfolder.absolute_url())

        # the 'member home' link that follows is deprecated by the new profile view
        #member_folder = self.memberInfoView.member_folder
        #if member_folder is None:
        #    member_folder = self.mtool.getHomeFolder(self.memberInfoView.member.getId())
        #if member_folder is not None: # why isn't this an 'else:'?
        #    self.addMenuItem('Member Home', 
        #                     member_folder.absolute_url())

    def addProjectView(self):
        projectInfoView = self.projectInfoView
        proj_home_url = projectInfoView.project.absolute_url()
        self.addMenuItem('project home', proj_home_url)
        self.addMenuItem('contents', '/'.join((proj_home_url, 'folder_contents')))
        self.addMenuItem('contact', '/'.join((proj_home_url, 'contact_project_admins')))

        supporter = IFeatureletSupporter(projectInfoView.project)

        for i in supporter.getInstalledFeatureletIds():
            desc = supporter.getFeatureletDescriptor(i)
            self.addMenuItem(desc['content'][0]['title'],
                             '/'.join((proj_home_url, desc['content'][0]['id'])))
        
        if projectInfoView.projectMembership:
            self.addMenuItem('preferences', '/'.join((proj_home_url, 'base_edit')))

    def menuItems(self):
        """
        return a function that indicates what menu items the user should be seeing
        """
        projectInfoView = queryMultiAdapter((self._context[0],
                                             self.request),
                                            name='project_info')
        memberInfoView = queryMultiAdapter((self._context[0],
                                            self.request),
                                           name='member_info')

        if projectInfoView is not None and projectInfoView.inProject:
            self.projectInfoView = projectInfoView
            self.addProjectView()
        if memberInfoView is not None:
            if memberInfoView.inMemberArea or memberInfoView.inMemberObject:
                self.memberInfoView = memberInfoView
                if memberInfoView.inPersonalArea or memberInfoView.inSelf:
                    self.addPersonalView()
                else:
                    self.addMemberView()

        return self.menu_items
