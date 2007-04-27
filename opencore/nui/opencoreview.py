"""
OpenCore Base View
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

    def magic(self):
        if self.inProject():
            return nui.renderView(self.getViewByName('oc-project'))
        elif self.inMemberArea():
            return "@@magic knows you're in a member area"
        else:
            return "@@magic doesn't know where you are"

    def transclude(self):
        return self.request.get_header('X-transcluded')

    def include(self, viewname):
        if self.transclude():
            return '<a href="@@%s" rel="include">%s</a>\n' % (viewname, viewname)
        return nui.renderView(self.getViewByName(viewname))

    def getViewByName(self, viewname):
        return self.context.unrestrictedTraverse('@@' + viewname)

    def renderTemplate(self, headviews='', bodyviews=''):
        head = nui.renderView(self.getViewByName('oc-globalhead'))
        for i in headviews:
            head += nui.renderView(self.getViewByName(i))
        head = nui.wrapWithTag(head, 'head')

        body = ''
        for i in bodyviews:
            body += self.include(i)
        body = nui.wrapWithTag(body, 'div', 'content-container')
        body += self.include('oc-footer')
        body = self.include('oc-topnav') + body
        body = nui.wrapWithTag(body, 'div', 'page-container')
        body = nui.wrapWithTag(body, 'body')

        return '\n'.join((head, body))

    def isUserLoggedIn(self):
        # TODO
        return False

    def topnavLinks(self):
        text = ['people', 'projects']
        urls = ['/people', '/projects']
        if self.isUserLoggedIn():
            text += ['start a project', 'someuser', 'log out']
            urls += ['/projects/add_project', '/people/someuser', '/logout']
        else:
            text += ['log in/join']
            urls += ['/loginjoin_form']
        urls = map(lambda url: self.siteURL + url, urls)
        return [dict(url=url, text=text) for url, text in zip(urls, text)]

    def subnavLinks(self):
        if self.inProject():
            projURL = '/'.join((self.siteURL, 'projects', self.projectNavName()))
            text = ['home', 'contents', 'contact']
            urls = [projURL + i for i in ['', '/folder_contents', '/contact_project_admins']]
            if self.userHasEditPrivs():
                text += ['project preferences', 'team preferences']
                urls += [projURL + '/edit', '%s/portal_teams/%s' % (self.siteURL, self.projectNavName())]
        else: # TODO
            text = ['aSubnavLink']
            urls = [self.siteURL]
        return [dict(url=url, text=text) for url, text in zip(urls, text)]

    def userHasEditPrivs(self):
        """Returns true iff user has edit privileges on this view."""
        # TODO
        return False

    def tabs(self):
        def isSelected(taburl):
            if False: # TODO... self.context == self.context.unrestrictedTraverse(taburl) ???
                return 'selected'
        def isDisabled(tabRequiresEdit):
            if not (tabRequiresEdit and self.userHasEditPrivs()):
                return 'disabled'
        def getCssClass(taburl, tabRequiresEdit):
            return isSelected(taburl) or isDisabled(tabRequiresEdit) or ''
        names = ['view', 'edit', 'history']
        requiresEditPrivs = [False, True, True]
        urls = ['/'.join((self.url, i)) for i in names] # XXX
        classes = map(getCssClass, urls, requiresEditPrivs)
        return [dict(name=name, url=url, cssclass=cssclass) for
            name, url, cssclass in zip(names, urls, classes)]

    def renderLastModifiedInfo(self):
        # TODO
        return ''

    def inProject(self):
        # TODO
        return self.piv.inProject

    def inMemberArea(self):
        # TODO
        return self.miv.inMemberArea

    def project(self):
        # TODO
        return self.piv.project

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
            else:
                # TODO
                print """Unexpected error in OpencoreView.currentProjectPage:
                self.context is neither an OpenProject nor an OpenPage"""
                import pdb; pdb.set_trace()

    def renderProjectContent(self):
        return nui.renderOpenPage(self.currentProjectPage())
            
    def featurelets(self):
      # TODO
      names = []
      urls = []
      return zip(names, urls)

    def titles(self):
        if self.inProject():
            title = self.projectFullName()
            subtitle = self.currentProjectPage().title
        elif self.inMemberArea():
            title = self.miv.membername
            subtitle = 'some subtitle for a member area page' #TODO
        else:
            title = self.context.title
            subtitle = 'what should the subtitle be for this page?' #TODO
        return title, subtitle

    def renderWindowTitle(self):
        title, subtitle = self.titles()
        title, subtitle = truncate(title, max=16), truncate(subtitle, max=24)
        windowtitle = [subtitle, title, self.sitetitle]
        return nui.windowTitleSeparator.join([i for i in windowtitle if i])

    def renderTopnavTitle(self):
        title = self.titles()[0]
        title = truncate(title, max=64)
        h1 = '<h1>%s</h1>' % title
        return '<a href="%s">%s</a>' % (self.url, h1)

    def renderPageTitle(self):
        """Renders the page's subtitle in <a><h1> tags"""
        subtitle = self.titles()[1]
        subtitle = truncate(subtitle, max=256)
        return '<a href="%s">%s</a>' % (self.url, subtitle)

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
