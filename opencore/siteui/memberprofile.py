"""
Profile View

@@ tests?
"""
from AccessControl import allow_module

from Products.CMFCore.utils import getToolByName 
from Products.Five import BrowserView
from interfaces import IMemberHomePage
from interfaces import IMemberFolder
from interfaces import IFirstLoginEvent
from zope.interface import implements, alsoProvides
from memberinfo import MemberInfoView
from zope.event import notify

# XXX this is too promiscuous, we should move fireFirstLoginEvent into
# its own module so we don't need to expose the rest of this to TTW
# code

# @@ wouldn't worry about it. you don't do anything in this
# module that would compromise security

allow_module('opencore.siteui.memberprofile')


class ProfileView(BrowserView):
    implements(IMemberHomePage)
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.request.set('disable_border', 1)
        self.mtool = getToolByName(self.context, 'portal_membership')
        self.mdtool = getToolByName(self.context, 'portal_memberdata')
        self.miv = MemberInfoView(context, request)
        self.member = self.miv.member
        self.memberlogin = self.member.getId()
        self.memberfolder = self.miv.member_folder
        self.info = None

    def getUserInfo(self):
        """Returns a dict with user info that gets displayed on profile view"""
        if self.info is None:

            self.info = dict(member=self.member,
                             login=self.memberlogin,
                             fullname=self.member.fullname,
                             location=self.member.getLocation(),
                             prefsurl=self.member.absolute_url() + '/edit',
                             portrait=self.member.getPortrait(),
                             projects=self.member.getProjectListing(), # @@@ this should be indexed and then returned by a catalog call
                             wiki=getattr(self.memberfolder, '%s-home' % self.memberlogin).CookedBody(),
                             editpermission=self.mtool.checkPermission('Modify portal content', self.context)
                             )
        return self.info


class FirstLoginEvent(object):
    implements(IFirstLoginEvent)
    def __init__(self, member):
        self.member = member


def notifyFirstLogin(member):
    notify(FirstLoginEvent(member))


def create_home_directory(event):
    # TODO write tests

    member = event.member
    mtool = getToolByName(member, 'portal_membership')
    member_id = member.getId()

    folder = mtool.getHomeFolder(member_id)
    alsoProvides(folder, IMemberFolder)

    page_id = "%s-home" % member_id
    title = "%s Home" % member_id
    folder.invokeFactory('Document', page_id, title=title)
    folder.setDefaultPage(page_id)
    
    page = getattr(folder, page_id)
    # XXX acquisition, ugh @@ huh?
    page_text = member.member_index(member_id=member_id)
    page.setText(page_text)

    # the page is the homepage
    alsoProvides(page, IMemberHomePage)

    # make profile the default view on the homepage
    page.setLayout('profile.html')
