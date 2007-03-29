"""
Profile View
"""
# TODO write tests

from AccessControl import allow_module

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ModifyPortalContent
from Products.Five import BrowserView

from zope.interface import implements, alsoProvides
from zope.event import notify
from zope.component import getMultiAdapter, adapts

from memberinfo import MemberInfoView

from interfaces import IMemberHomePage
from interfaces import IMemberFolder
from interfaces import IFirstLoginEvent

from topp.utils.pretty_date import prettyDate

from opencore import redirect 
from opencore.redirect import IRedirected 
from opencore.interfaces import IProject 

allow_module('opencore.siteui.memberprofile')

class ProfileView(BrowserView):
    implements(IMemberHomePage)
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.request.set('disable_border', 1)
        self.info = None


    def _getPortraitURL(self, member):
        portrait = member.getProperty('portrait', None)
        return portrait and portrait.absolute_url()


    def _getWiki(self, memberfolder):
        homepage_id = memberfolder.getDefaultPage()
        if homepage_id is not None:
            homepage = memberfolder._getOb(homepage_id)
            return homepage.CookedBody()
        return ''


    def getUserInfo(self):
        """Returns a dict with user info that gets displayed on profile view"""
        if self.info is None:
            mtool = getToolByName(self.context, 'portal_membership')
            miv = getMultiAdapter((self.context, self.request), name='member_info')
            member, memberfolder = miv.member, miv.member_folder
            self.info = dict(login=member.getId(),
                             fullname=member.getFullname(),
                             membersince=prettyDate(member.created()),
                             lastlogin=prettyDate(member.getLast_login_time()),
                             location=member.getLocation(),
                             prefsurl=member.absolute_url() + '/edit',
                             portraiturl=self._getPortraitURL(member),
                             projects=member.getProjects(), # @@@ this should be indexed and then returned by a catalog call
                             wiki=self._getWiki(memberfolder),
                             editpermission=mtool.checkPermission(ModifyPortalContent, self.context),
                             isme=member == mtool.getAuthenticatedMember()
                             )
        return self.info

    def getLatestContent(self, limit_per_type=5):
        catalog = getToolByName(self.context, 'portal_catalog')
        types = ('OpenProject', 'Document')

        userinfo = self.getUserInfo()

        found = {}
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
    def __init__(self, member, request):
        self.member = member
        self.request = request

def notifyFirstLogin(member, request):
    notify(FirstLoginEvent(member, request))


def create_home_directory(event):
    # TODO write tests

    member = event.member
    mtool = getToolByName(member, 'portal_membership')
    member_id = member.getId()

    folder = mtool.getHomeFolder(member_id)
    maybe_apply_member_folder_redirection(folder, event.request)
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



def maybe_apply_member_folder_redirection(folder, request):
    if not request or not 'PARENTS' in request:
        return

    parents = request['PARENTS']

    for parent in parents:
        # check the request for a redirected project
        if (IRedirected.providedBy(parent) and
            IProject.providedBy(parent)):
            # yes, so apply redirection to the folder
            apply_member_folder_redirection(folder, parent)
            break

def apply_member_folder_redirection(folder, parent):
    parent_info = redirect.get_info(parent)
    folder_id = folder.getId()
    folder_path = "%s/people/%s" % (parent_info.url, folder_id)
    redirect.activate(folder, url=folder_path)


