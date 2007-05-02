"""
OpencoreView: the base view for all of opencore's new zope3 views.
"""
import nui

from opencore.content.page import OpenPage
from opencore.content.member import OpenMember
from Products.OpenPlans.content.project import OpenProject
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from memojito import memoizedproperty, memoize
from opencore import redirect 
from opencore.interfaces import IProject 
from topp.utils.pretty_date import prettyDate
from topp.utils.pretty_text import truncate
from zope.component import getMultiAdapter, adapts, adapter

class OpencoreView(BrowserView):

    def __init__(self, context, request):
        self.context      = context
        self.request      = request
        self.membranetool = getToolByName(context, 'membrane_tool')
        self.membertool   = getToolByName(context, 'portal_membership')
        self.catalogtool  = getToolByName(context, 'portal_catalog')
        self.portal       = getToolByName(context, 'portal_url').getPortalObject()
        self.sitetitle    = self.portal.title
        self.siteURL      = self.portal.absolute_url()
        self.logoURL      = nui.logoURL
        self.piv = context.unrestrictedTraverse('project_info') # TODO don't rely on this
        self.miv = context.unrestrictedTraverse('member_info')  # TODO don't rely on this

    def transclude(self):
        return self.request.get_header('X-transcluded')

    def magicTopnavSubcontext(self):
        if self.inProject():
            return 'oc-topnav-subcontext-project'
        elif self.inUserArea():
            return 'oc-topnav-subcontext-user'
        return 'oc-blank'

    def magicContent(self):
        if self.inProject():
            return 'oc-project-view'
        elif self.inUserArea():
            return 'oc-user-profile'
        return 'oc-blank'

    def renderTopnavSubcontext(self, viewname):
        viewname = viewname or self.magicTopnavSubcontext()
        return nui.renderView(self.getViewByName(viewname))

    def renderContent(self, viewname):
        viewname = viewname or self.magicContent()
        return nui.renderView(self.getViewByName(viewname))

    def include(self, viewname):
        if self.transclude():
            return nui.renderTranscluderLink(viewname)
        return nui.renderView(self.getViewByName(viewname))

    def getViewByName(self, viewname):
        return self.context.unrestrictedTraverse('@@' + viewname)
    
    @property
    def userobj(self):
        return self.membertool.getAuthenticatedMember()

    @property
    def loggedin(self):
        return self.userobj.getId() is not None

    @property
    def user(self):
        """Returns a dict containing information about the
        currently-logged-in user for easy templates access.
        If no user is logged in, there's just less info to return."""
        if self.loggedin:
            usr = self.userobj
            canedit = self.membertool.checkPermission(ModifyPortalContent, self.context) and True or False
            return dict(id=usr.getId(), fullname=usr.fullname,
                        profileurl=usr.absolute_url(),
                        lastlogin=usr.getLast_login_time(),
                        canedit=canedit)
        return dict(canedit=False)
    @property
    def loggedin(self):
        return self.membertool.getAuthenticatedMember().getId() is not None

    def viewed_user(self): # TODO
        """Returns the user found in the context's acquisition chain, if any."""
        return self.miv.member

    def inProject(self): # TODO
        return self.piv.inProject

    def inUserArea(self): # TODO
        return self.miv.inMemberArea

    def project(self): # TODO
        return self.piv.project

    def projectURL(self):
        return self.project().absolute_url()

    def projectHomePageURL(self):
        return self.projectHomePage().absolute_url()

    def projectNavName(self):
        return self.project().getId()

    def projectFullName(self):
        return self.project().getFull_name()

    def projectHomePage(self):
        if self.inProject():
            homepagename = self.project().getDefaultPage()
            return self.project().unrestrictedTraverse(homepagename)

    def currentProjectPage(self):
        if self.inProject():
            if isinstance(self.context, OpenProject):
                return self.projectHomePage()
            elif isinstance(self.context, OpenPage):
                return self.context
            else: # TODO
                return 'Unexpected error in OpencoreView.currentProjectPage: ' \
                       'self.context is neither an OpenProject nor an OpenPage'

    def renderProjectContent(self):
        return nui.renderOpenPage(self.currentProjectPage())
            
    def featurelets(self): # TODO
        names = []
        urls = []
        return zip(names, urls)

    def pageTitle(self):
        if self.inProject():
            return self.currentProjectPage().title
        else: # TODO
            return ''

    def areaTitle(self):
        if self.inProject():
            return self.projectFullName()
        if self.inUserArea():
            return self.viewed_user.fullname
        else: # TODO
            return ''

    def pageURL(self):
        if self.inProject():
            return self.currentProjectPage().absolute_url()
        else: # TODO
            return ''

    def areaURL(self):
        if self.inProject():
            return self.projectURL()
        if self.inUserArea():
            return self.user['profileurl']
        else: # TODO
            return ''

    def windowTitle(self):
        pagetitle, areatitle = self.pageTitle(), self.areaTitle()
        pagetitle, areatitle = truncate(pagetitle, max=24), truncate(areatitle, max=16)
        titles = [pagetitle, areatitle, self.sitetitle]
        return nui.windowTitleSeparator.join([i for i in titles if i])

    def nusers(self):
        """Returns the number of users of the site."""
        all_users = self.membranetool(getId='')
        return len(all_users)

    def nprojects(self):
        """Returns the number of projects hosted by the site."""
        all_projects = self.catalogtool(portal_type='OpenProject')
        return len(all_projects)

    def dob(self):
        """Returns OpenPlans' "date of birth"."""
        # TODO
        return 'January 3, 1937'

    def lastModifiedOn(self): # TODO
        return '1/13/37'

    def lastModifiedBy(self): # TODO
        return 'jab'


class YourProjectsView(OpencoreView):
    def __init__(self, context, request):
        OpencoreView.__init__(self, context, request)
        self.member = self.membertool.getAuthenticatedMember()


    def get_projects_for_user(self):
        projects = self.member.getProjectListing()

        out = []
        for project in projects:
            roles = ', '.join(project.getTeamRolesForAuthMember())
            teams = project.getTeams()
            for team in teams:
                # eventually this will be 1:1 relationship, project:team
                mship = team.getMembershipByMemberId(self.member.getId())
                if mship is not None:
                    created = mship.created()

            out.append({'title':project.title, 'role':roles, 'since':created, 'status':'not set'})

        return out

    def get_invitations_for_user(self):
        invites = []
        invites.append({'name':'Big Animals'})
        invites.append({'name':'Small Animals'})
        return invites
