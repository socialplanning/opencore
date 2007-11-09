from zope.component import queryMultiAdapter
from zope.component import getUtility

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ModifyPortalContent
from Products.Five.viewlet.viewlet import ViewletBase

from Products.OpenPlans.permissions import CopyOrMove

from opencore.interfaces import IProject

from topp.featurelets.interfaces import IFeatureletSupporter


class MenuItem(object):
    """ a simple class that contains minimal info about menu items """

    title=''
    action=''
    description=''

    def __init__(self, title='', action='', description=''):
          self.title=title
          self.action=action
          self.description=description

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
        self.addMenuItem('My Profile', homefolder.absolute_url())
        self.addMenuItem('My Preferences', '%s/edit' % member.absolute_url())

    def addMemberView(self):
        mem_id = self.memberInfoView.member.getId()
        memberfolder = self.memberInfoView.member_folder or \
                       self.mtool.getHomeFolder(mem_id)
        if memberfolder:
            self.addMenuItem('Member Profile', memberfolder.absolute_url())

    def addProjectView(self):
        projectInfoView = self.projectInfoView
        project = projectInfoView.project
        proj_home_url = project.absolute_url()
        self.addMenuItem('Project Home', proj_home_url)

        if self.mtool.checkPermission(CopyOrMove, project):
            self.addMenuItem('Contents',
                             '%s/folder_contents' % proj_home_url)

        self.addMenuItem('Contact',
                         '%s/contact_project_admins' % proj_home_url)

        supporter = IFeatureletSupporter(projectInfoView.project)

        for i in supporter.getInstalledFeatureletIds():
            desc = supporter.getFeatureletDescriptor(i)
            self.addMenuItem(desc['menu_items'][0]['title'],
                             '%s/%s' % (proj_home_url,
                                        desc['menu_items'][0]['action']))

        if self.mtool.checkPermission(ModifyPortalContent, project):
            self.addMenuItem('Preferences', '%s/edit' % proj_home_url)

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
