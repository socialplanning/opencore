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
from memojito import memoize, memoizedproperty
from opencore import redirect 
from opencore.interfaces import IProject 
from zope.component import getMultiAdapter, adapts, adapter
from topp.utils.pretty_text import truncate
from opencore.nui.static import render_static
from topp.featurelets.interfaces import IFeatureletSupporter

class OpencoreView(BrowserView):
    def __init__(self, context, request):
        self.context      = context
        self.request      = request
        self.transcluded  = request.get_header('X-transcluded')
        self.membranetool = getToolByName(context, 'membrane_tool')
        self.membertool   = getToolByName(context, 'portal_membership')
        self.catalogtool  = getToolByName(context, 'portal_catalog')
        self.portal       = getToolByName(context, 'portal_url').getPortalObject()
        self.sitetitle    = self.portal.title
        self.siteURL      = self.portal.absolute_url()
        self.logoURL      = nui.logoURL
        self.dob          = nui.dob
        self.piv = context.unrestrictedTraverse('project_info') # TODO don't rely on this
        self.miv = context.unrestrictedTraverse('member_info')  # TODO don't rely on this
        self.errors = {}
        self.render_static = render_static

    def portal_status_message(self):
        plone_utils = getToolByName(self.context, 'plone_utils')
        msgs = plone_utils.showPortalMessages()
        msgs = [msg.message for msg in msgs]
        return msgs

    def addPortalStatusMessage(self, msg):
        plone_utils = getToolByName(self.context, 'plone_utils')
        from Products.CMFPlone import PloneMessageFactory
        plone_utils.addPortalMessage(PloneMessageFactory(msg))

    def include(self, viewname):
        if self.transcluded:
            return nui.renderTranscluderLink(viewname)
        return nui.renderView(self.getViewByName(viewname))

    def magicTopnavSubcontext(self): # TODO get rid of magic inference
        if self.inproject():
            return 'oc-topnav-subcontext-project'
        elif self.inuser():
            return 'oc-topnav-subcontext-user'
        return 'oc-blank'

    def magicContent(self): # TODO get rid of magic inference
        if self.inproject():
            return 'oc-project-view'
        elif self.inuser():
            return 'oc-user-profile'
        return 'oc-blank'

    def renderTopnavSubcontext(self, viewname):
        viewname = viewname or self.magicTopnavSubcontext()
        return nui.renderView(self.getViewByName(viewname))

    def renderContent(self, viewname):
        viewname = viewname or self.magicContent()
        return nui.renderView(self.getViewByName(viewname))

    def renderProjectContent(self):
        return nui.renderOpenPage(self.currentProjectPage())

    def getViewByName(self, viewname):
        return self.context.unrestrictedTraverse('@@' + viewname)


    def projectobj(self): # TODO
        return self.piv.project

    def userobj(self):
        return self.membertool.getAuthenticatedMember()

    def loggedin(self):
        return self.userobj().getId() is not None

    def inproject(self): # TODO
        return self.piv.inProject

    def inuser(self): # TODO
        return self.miv.inMemberArea
    
    def vieweduser(self): # TODO
        """Returns the user found in the context's acquisition chain, if any."""
        return self.miv.member

    def pagetitle(self):
        if self.inproject():
            return self.currentProjectPage().title
        return self.context.title # TODO?

    def areatitle(self):
        if self.inproject():
            return self.project()['fullname']
        if self.inuser():
            return self.vieweduser().fullname
        return self.context.title # TODO?

    def windowtitle(self):
        pagetitle, areatitle = truncate(self.pagetitle(), max=24), \
                               truncate(self.areatitle(), max=16)
        titles = [pagetitle, areatitle, self.sitetitle]
        return nui.windowTitleSeparator.join([i for i in titles if i])

    def pageURL(self):
        if self.inproject():
            return self.currentProjectPage().absolute_url()
        return self.context.absolute_url() # TODO?

    def areaURL(self):
        if self.inproject():
            return self.project()['url']
        if self.inuser():
            return self.user()['url']
        else: # TODO
            return ''


    def nusers(self): # TODO cache
        """Returns the number of users of the site."""
        users = self.membranetool(getId='')
        return len(users)

    def nprojects(self): # TODO cache
        """Returns the number of projects hosted by the site."""
        projects = self.catalogtool(portal_type='OpenProject')
        return len(projects)

    def user(self):
        """Returns a dict containing information about the
        currently-logged-in user for easy template access.
        If no user is logged in, there's just less info to return."""
        if self.loggedin():
            usr = self.userobj()
            id = usr.getId()
            user_dict = dict(id=id,
                             fullname=usr.fullname,
                             url=self.membertool.getHomeUrl(),
                             )
            # XXX admins don't have as many properties, so we have a special case for them
            # right now checking for string 'admin', we should check if the user has the right role instead
            if id == 'admin':
                user_dict['canedit'] = True
                return user_dict
            else:
                canedit = bool(self.membertool.checkPermission(ModifyPortalContent, self.context))
                user_dict.update(dict(canedit=canedit,
                                      lastlogin=usr.getLast_login_time(),
                                      ))
                return user_dict
        return dict(canedit=False)

    def project(self): # TODO
        """Returns a dict containing information about the
        currently-viewed project for easy template access."""
        if self.inproject():
            proj = self.projectobj()
            return dict(navname=proj.getId(),
                        fullname=proj.getFull_name(),
                        url=proj.absolute_url(), # XXX use self.projectHomePage.absolute_url() instead?
                        home=self.projectHomePage(),
                        mission=proj.Description(),
                        security=2, # where, in unix speak, 1 = 660, 2 = 664, 3 = 666, 0 = 1 with no search results
                        featurelets=self.projectFeaturelets())

    def page(self): # TODO
        """Returns a dict containing information about the
        currently-viewed page for easy template access."""
        if self.inproject():
            page = self.currentProjectPage()
            lastModifiedOn = '1/13/37'
            lastModifiedBy = 'jab'
            if page:
                return dict(title=page.title,
                            url=page.absolute_url(),
                            lastModifiedOn=lastModifiedOn,
                            lastModifiedBy=lastModifiedBy)


    def projectHomePage(self):
        if self.inproject():
            homepagename = self.projectobj().getDefaultPage()
            return self.projectobj().unrestrictedTraverse(homepagename)

    def projectFeaturelets(self):
        fletsupporter = IFeatureletSupporter(self.context)
        featurelet_ids = fletsupporter.getInstalledFeatureletIds()
        featurelets = [{'name': id, 'url' : fletsupporter.getFeatureletDescriptor(id)['content'][0]['id']} for id in featurelet_ids]
        return featurelets

    def currentProjectPage(self):
        if self.inproject():
            if isinstance(self.context, OpenProject):
                return self.projectHomePage()
            elif isinstance(self.context, OpenPage):
                return self.context
            else: # TODO
                return 'Unexpected error in OpencoreView.currentProjectPage: ' \
                       'self.context is neither an OpenProject nor an OpenPage'
    
    def user_exists(self, username):
        users = self.membranetool(getId=username)
        return len(users) > 0

    def userExists(self):
        username = self.request.get("username")
        if username is not None:
            return self.user_exists(username)
        return False

class YourProjectsView(OpencoreView):

    def get_projects_for_user(self):
        member = self.userobj()
        id = member.getId()
        if id is None: return []
        projects = member.getProjectListing()
        out = []
        for project in projects:
            roles = ', '.join(project.getTeamRolesForAuthMember())
            teams = project.getTeams()
            for team in teams:
                # eventually this will be 1:1 relationship, project:team
                mship = team.getMembershipByMemberId(id)
                if mship is not None:
                    created = mship.created()

            out.append({'title':project.title, 'role':roles, 'since':created, 'status':'not set'})
        return out

    def get_invitations_for_user(self):
        invites = []
        invites.append({'name':'Big Animals'})
        invites.append({'name':'Small Animals'})
        return invites
