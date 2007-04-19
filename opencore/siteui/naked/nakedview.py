"""
Naked Base View
"""
from sitewide import windowTitleSeparator, topplogo

from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from memojito import memoizedproperty, memoize
from opencore import redirect 
from opencore.interfaces import IProject 
from topp.utils.pretty_date import prettyDate
from topp.utils.pretty_text import truncate
from zope.component import getMultiAdapter, adapts, adapter

class NakedView(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.topplogo = topplogo
        self.portal = getToolByName(context, 'portal_url').getPortalObject() 
        self.url = context._getURL()
        self.siteurl = self.portal.absolute_url()
        self.piv = context.unrestrictedTraverse('project_info') # TODO don't rely on this
        self.miv = context.unrestrictedTraverse('member_info')  # TODO don't rely on this

    def _transclude(self):
        return self.request.get_header('X-transcluded')

    def include(self, viewname):
        if self._transclude():
            return '<a href="%s" rel="include">%s</a>' % (viewname, viewname)
        return self.context.unrestrictedTraverse(viewname).index()

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
        urls = map(lambda url: self.siteurl + url, urls)
        return [dict(url=url, text=text) for url, text in zip(urls, text)]

    def subnavLinks(self):
        if self.inProject():
            text = ['home', 'contents', 'contact']
            urls = ['', '/folder_contents', '/contact_project_admins']
            if self.userHasEditPrivs():
                text += ['project preferences', 'team preferences']
                urls += ['/edit', '%s/portal_teams/%s' % (self.siteurl, self.projectNavName())]
        else: # TODO
            text = ['morx']
            urls = ['/morx']
        urls = map(lambda url: self.siteurl + url, urls)
        return [dict(url=url, text=text) for url, text in zip(urls, text)]

    def userHasEditPrivs(self):
        """Returns true iff user has edit privileges on this view."""
        # TODO
        return False

    def tabs(self):
        # XXX code review
        def isSelected(taburl):
            if True: #TODO self.context == self.context.unrestrictedTraverse(taburl):
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

    def project(self):
        # TODO
        return self.piv.project

    def projectNavName(self):
        return self.project().Title()

    def projectFullName(self):
        return self.project().getFull_name()

    def featurelets(self):
      # TODO
      names = []
      urls = []
      return zip(names, urls)

    def titleInfo(self):
        if self.inProject():
            title = self.piv.fullname
            subtitle = self.context.title
        elif self.miv.inMemberArea:
            title = self.miv.membername
            subtitle = 'foo' #TODO
        else:
            title = self.context.title
            subtitle = 'bar' #TODO
        return title, subtitle

    def renderWindowTitle(self):
        title, subtitle = self.titleInfo()
        title, subtitle = truncate(title, max=16), truncate(subtitle, max=24)
        windowtitle = [subtitle, title, self.portal.title]
        return windowTitleSeparator.join([i for i in windowtitle if i])

    def renderTopnavTitle(self):
        title, _ = self.titleInfo()
        title = truncate(title, max=64)
        h1 = '<h1>%s</h1>' % title
        return '<a href="%s">%s</a>' % (self.context.absolute_url(), h1)

    def renderPageTitle(self):
        _, subtitle = self.titleInfo()
        subtitle = truncate(subtitle, max=256)
        return '<a href="%s">%s</a>' % (self.context.absolute_url(), subtitle)

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
