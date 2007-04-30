"""
OpencoreView: the base view for all of opencore's new z views.
"""
import nui

from opencore.content.page import OpenPage
from Products.OpenPlans.content.project import OpenProject
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
        portal = getToolByName(context, 'portal_url').getPortalObject()
        self.context = context
        self.request = request
        self.logoURL = nui.logoURL
        self.siteURL = portal.absolute_url()
        self.sitetitle = portal.title
        self.url = context.absolute_url()
        self.piv = context.unrestrictedTraverse('project_info') # TODO don't rely on this
        self.miv = context.unrestrictedTraverse('member_info')  # TODO don't rely on this

    def transclude(self):
        return self.request.get_header('X-transcluded')

    def magicTopnavSubcontext(self):
        if self.inProject():
            return 'oc-topnav-subcontext-project'
        return 'oc-blank'

    def magicContent(self):
        if self.inProject():
            return 'oc-project-view'
        return 'oc-blank'

    def renderTopnavSubcontext(self, viewname):
        if not viewname:
            viewname = self.magicTopnavSubcontext()
        return nui.renderView(self.getViewByName(viewname))

    def renderContent(self, viewname):
        if not viewname:
            viewname = self.magicContent()
        return nui.renderView(self.getViewByName(viewname))

    def include(self, viewname):
        if self.transclude():
            return nui.renderTranscluderLink(viewname)
        return nui.renderView(self.getViewByName(viewname))

    def getViewByName(self, viewname):
        return self.context.unrestrictedTraverse('@@' + viewname)

    def isUserLoggedIn(self): # TODO
        return False

    def userHasEditPrivs(self): # TODO
        """Returns true iff user has edit privileges on this view."""
        return False

    def lastModifiedOn(self): # TODO
        return '1/13/37'

    def lastModifiedBy(self): # TODO
        return 'joetestuser'

    def inProject(self): # TODO
        return self.piv.inProject

    def inMemberArea(self): # TODO
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
        else: # TODO
            return ''

    def windowTitle(self):
        pagetitle, areatitle = self.pageTitle(), self.areaTitle()
        pagetitle, areatitle = truncate(pagetitle, max=24), truncate(areatitle, max=16)
        titles = [pagetitle, areatitle, self.sitetitle]
        return nui.windowTitleSeparator.join([i for i in titles if i])

    def nmembers(self):
        """Returns the number of members of the site."""
        # TODO
        return 1337

    def nprojects(self):
        """Returns the number of projects hosted by the site."""
        # TODO
        return 1337

    def dob(self):
        """Returns OpenPlans' "date of birth"."""
        # TODO
        return 'January 3, 1937'
