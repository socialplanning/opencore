from zope.viewlet.viewlet import ViewletBase
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName
from opencore.interfaces import IMemberFolder
from opencore.interfaces import IProject
from opencore.interfaces import IOpenPage
from opencore.interfaces.adding import IAddProject
from opencore.interfaces.adding import IAmAPeopleFolder

class BaseMenuItem(ViewletBase):
    """Base class for topnav menu items."""

    name = u''
    url = '#'
    css_class = None

    def update(self):
        """subclasses can control setting state here"""

    def __cmp__(self, rhs):
        #XXX this ideally would have happened
        # with a custom sorting viewlet manager
        # but a security error was being raised
        return cmp(self.__name__, rhs.__name__)

    def _item_providing(self, iface):
        chain = self.context.aq_inner.aq_chain
        for item in chain:
            if iface.providedBy(item):
                return item

    render = ZopeTwoPageTemplateFile('topnav_menuitem.pt')

# Member menu items
class MemberWikiMenuItem(BaseMenuItem):
    name = u'Wiki'

    def update(self):
        mem = self._item_providing(IMemberFolder)
        if mem is None:
            self.render = lambda *a:''
            return
        self.url = '%s/%s-home' % (mem.absolute_url(), mem.getId())
        if IOpenPage.providedBy(self.context):
            self.css_class = 'oc-topnav-selected'

class MemberMenuItem(BaseMenuItem):
    """Base class to allow easy creation of member menu items"""
    item_url = '#'

    def update(self):
        mem = self._item_providing(IMemberFolder)
        if mem is None:
            self.render = lambda *a:''
            return
        self.url = '%s/%s' % (mem.absolute_url(), self.item_url)
        if self.request.ACTUAL_URL.startswith(self.url):
            self.css_class = 'oc-topnav-selected'

class ProfileMenuItem(MemberMenuItem):
    name = u'Profile'
    item_url = 'profile'

class AccountMenuItem(MemberMenuItem):
    name = u'Account'
    item_url = 'account'

# Project menu items
class ProjectWikiMenuItem(BaseMenuItem):
    name = u'Wiki'

    def update(self):
        proj = self._item_providing(IProject)
        if proj is None:
            self.render = lambda *a:''
            return
        self.url = '%s/project-home' % proj.absolute_url()
        if IOpenPage.providedBy(self.context):
            self.css_class = 'oc-topnav-selected'

class ProjectMenuItem(BaseMenuItem):
    """Base class to allow easy creation of project mneu items"""
    item_url = '#'

    def update(self):
        proj = self._item_providing(IProject)
        if proj is None:
            self.render = lambda *a:''
            return
        self.url = '%s/%s' % (proj.absolute_url(), self.item_url)
        if self.request.ACTUAL_URL.startswith(self.url):
            self.css_class = 'oc-topnav-selected'

class TeamMenuItem(ProjectMenuItem):
    name = u'Team'
    item_url = 'team'

class ManageTeamMenuItem(ProjectMenuItem):
    name = u'Manage Team'
    item_url = 'manage-team'

class ContentsMenuItem(ProjectMenuItem):
    name = u'Contents'
    item_url = 'contents'

class PreferencesMenuItem(ProjectMenuItem):
    name = u'Preferences'
    item_url = 'preferences'

class JoinMenuItem(BaseMenuItem):
    name = u'Join Project'

    def update(self):
        proj = self._item_providing(IProject)
        if proj is None:
            self.render = lambda *a:''
            return
        mstool = getToolByName(proj, 'portal_membership')
        if not mstool.isAnonymousUser():
            mem = mstool.getAuthenticatedMember()
            team = proj.getTeams()[0]
            filter_states = tuple(team.getActiveStates()) + ('pending',)
            if mem.getId() in team.getMemberIdsByStates(filter_states):
                self.render = lambda *a:''
                return
        self.url = '%s/%s' % (proj.absolute_url(), 'request-membership')
        if self.request.ACTUAL_URL == self.url:
            self.css_class = 'oc-topnav-selected'
        else:
            self.css_class = 'oc-topnav-join'

# Search menu items
class PeopleMenuItem(BaseMenuItem):
    name = u'People'

    def update(self):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        self.url = portal.people.absolute_url()
        if IAmAPeopleFolder.providedBy(self.context):
            self.css_class = 'oc-topnav-selected'

class ProjectsMenuItem(BaseMenuItem):
    name = u'Projects'

    def update(self):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        self.url = portal.projects.absolute_url()
        if (IAddProject.providedBy(self.context)
            and not self.request.ACTUAL_URL.endswith('/create')):
            self.css_class = 'oc-topnav-selected'

class StartProjectMenuItem(BaseMenuItem):
    name = u'Start A Project'

    def update(self):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        self.url = '%s/%s' % (portal.projects.absolute_url(), 'create')
        if self.request.ACTUAL_URL == self.url:
            self.css_class = 'oc-topnav-selected'


# Featurelets need to only provide
# name
# supp_must_provide - installed marker interface
# flet_url - portion of url after project url
class BaseFeatureletMenuItem(BaseMenuItem):
    """Base class to allow easy creation of featurelet menu items"""

    supporter = IProject
    supp_must_provide = None
    flet_url = '#'

    def update(self):
        proj = self._item_providing(self.supporter)
        if proj is None:
            self.render = lambda *a:''
            return
        if not self.supp_must_provide.providedBy(proj):
            self.render = lambda *a:''
            return

        self.url = '%s/%s' % (proj.absolute_url(), self.flet_url)
        if self.request.ACTUAL_URL.startswith(self.url):
            self.css_class = 'oc-topnav-selected'
