"""
Profile View

@@ tests?
"""
from AccessControl import allow_module

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ModifyPortalContent
from Products.Five import BrowserView

from zope.interface import implements, alsoProvides
from zope.event import notify
from zope.component import getMultiAdapter

from memberinfo import MemberInfoView

from interfaces import IMemberHomePage
from interfaces import IMemberFolder
from interfaces import IFirstLoginEvent

allow_module('opencore.siteui.memberprofile')

class ProfileView(BrowserView):
    implements(IMemberHomePage)
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.request.set('disable_border', 1)
        self.info = None

    def getUserInfo(self):
        """Returns a dict with user info that gets displayed on profile view"""
        if self.info is None:
            mtool = getToolByName(self.context, 'portal_membership')
            miv = getMultiAdapter((self.context, self.request),
                                  name='member_info')
            member = miv.member
            memberlogin = member.getId()
            memberfolder = miv.member_folder

            portrait_image = member.getProperty('portrait', None)
            portrait_url = portrait_image and portrait_image.absolute_url()

            homepage_id = memberfolder.getDefaultPage()
            if homepage_id is not None:
                homepage = memberfolder._getOb(homepage_id)
                wiki = homepage.CookedBody()
            else:
                wiki = ''

            editpermission = mtool.checkPermission(ModifyPortalContent,
                                                   self.context)

            isme = member == mtool.getAuthenticatedMember()

            self.info = dict(member=member,
                             login=memberlogin,
                             fullname=member.getFullname(),
                             location=member.getLocation(),
                             prefsurl=member.absolute_url() + '/edit',
                             portrait=member.getPortrait(), # XXX deprecated by portraiturl with NAKED
                             portraiturl=portrait_url,
                             projects=member.getProjects(), # @@@ this should be indexed and then returned by a catalog call
                             wiki=wiki,
                             editpermission=editpermission,
                             isme=isme,
                             )
        return self.info

    def getLatestContent(self, limit_per_type=5):
        catalog = getToolByName(self.context, 'portal_catalog')
        types = ('OpenProject', 'Document')

        userinfo = self.getUserInfo()

        found   = {}
        content = catalog.searchResults(Creator      = userinfo['login'],
                                        portal_type  = types,
                                        sort_on      = 'modified',
                                        sort_order   = 'reverse')

        for item in content:
            itemType = item.portal_type

            if not found.has_key(itemType):
                found[itemType] = []
            if len(found[itemType]) < limit_per_type:
                found[itemType].append(item)

        types = found.keys()
        types.sort()

        results = []

        for t in types:
            results.append({'portal_type' : t,
                            'content_items' : found[t]})

        return results
        

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
