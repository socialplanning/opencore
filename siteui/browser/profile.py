"""
Profile View
"""
from AccessControl import allow_module

from Products.CMFCore.utils import getToolByName 
from Products.Five import BrowserView
from interfaces import IMemberHomePage
from interfaces import IMemberFolder
from interfaces import IFirstLoginEvent
from zope.interface import implements, directlyProvides, alsoProvides
from memberinfo import MemberInfoView
from zope.event import notify

# XXX this is too promiscuous, we should move fireFirstLoginEvent into
#     its own module so we don't need to expose the rest of this to
#     TTW code
allow_module('Products.OpenPlans.browser.profile')


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
            self.info = {}
            self.info['member'] = self.member
            self.info['login'] = self.memberlogin
            self.info['fullname'] = self.member.fullname
            self.info['location'] = self.member.getLocation()
            self.info['portrait'] = self.member.getPortrait()
            self.info['projects'] = self.member.getProjectListing() # @@@ this should be indexed and then returned by a catalog call
            self.info['wiki'] = getattr(self.memberfolder, '%s-home' % self.memberlogin).CookedBody()
            self.info['editpermission'] = self.mtool.checkPermission('Modify portal content', self.context)
        return self.info


class FirstLoginEvent(object):
    implements(IFirstLoginEvent)
    def __init__(self, member):
        self.member = member


def fireFirstLoginEvent(member):
    notify(FirstLoginEvent(member))


def handleFirstLoginEvent(event):
    member = event.member
    mtool = getToolByName(member, 'portal_membership')
    member_id = member.getId()

    folder = mtool.getHomeFolder(member_id)
    directlyProvides(folder, IMemberFolder)
    alsoProvides(folder, IMemberHomePage)

    page_id = "%s-home" % member_id
    title = "%s Home" % member_id
    folder.invokeFactory('Document', page_id, title=title)
    # XXX how to make 'profile' the default view for the member folder?
    #folder.setDefaultPage(page_id)
    
    page = getattr(folder, page_id)
    # XXX acquisition, ugh
    page_text = member.member_index(member_id=member_id)
    page.setText(page_text)

    #directlyProvides(page, IMemberHomePage)
