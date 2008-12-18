"""
Profile View
"""
from AccessControl import allow_module
from Acquisition import aq_inner
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.remember.interfaces import IReMember
from opencore import redirect
from opencore.utils import interface_in_aq_chain
from opencore.interfaces import IProject, IConsumeNewMembers
from opencore.interfaces.event import IFirstLoginEvent
from opencore.interfaces.member import IMemberFolder, IMemberHomePage
from opencore.interfaces.member import IMemberInfo
from plone.memoize.instance import memoizedproperty
from topp.utils.pretty_date import prettyDate
from zope.component import getMultiAdapter, adapter
from zope.interface import implements, alsoProvides


allow_module('opencore.member.browser.miv')

class MemberInfoView(BrowserView):
    """A view which also provides contextual information about a member."""
    implements(IMemberInfo)

    def __init__(self, context, request):
        self._context = (context,)
        self.request = request
        self.mtool = getToolByName(context, 'portal_membership')

    @property
    def context(self):
        return self._context[0]

    def interfaceInAqChain(self, iface):
        return interface_in_aq_chain(aq_inner(self.context), iface)

    @memoizedproperty
    def member_folder(self):
        return self.interfaceInAqChain(IMemberFolder)

    @memoizedproperty
    def member_object(self):
        return self.interfaceInAqChain(IReMember)

    @memoizedproperty
    def member(self):
        """Returns the member object found by traversing the acquisition chain."""
        mf = self.member_folder
        if mf is not None:
            # XXX we shouldn't rely on the folder id matching the user id;
            #     maybe store the member id in an annotation on the folder?
            return self.mtool.getMemberById(mf.getId())
        return self.member_object

    @memoizedproperty
    def personal_folder(self):
        """Returns the folder of the authenticated member."""
        mem_id = self.mtool.getAuthenticatedMember().getId()
        return self.mtool.getHomeFolder(mem_id)

    @memoizedproperty
    def inMemberObject(self):
        return self.member_object is not None

    @memoizedproperty
    def inSelf(self):
        return self.inMemberObject and \
               self.member_object == self.mtool.getAuthenticatedMember()

    @property
    def inMemberArea(self):
        return self.member_folder is not None

    @memoizedproperty
    def inPersonalArea(self):
        return self.inMemberArea and self.member_folder == self.personal_folder


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
        

def initializeMemberArea(mtool, request, member_id=None):
    """
    This method is triggered by the 'notifyMemberAreaCreated' script
    that is called at the end of the membership tool's
    createMemberArea() method.  Will switch to an event as soon as the
    membership tool starts firing one.
    """
    if member_id:
        member = mtool.getMemberById(member_id)
    else:
        member = mtool.getAuthenticatedMember()
        member_id = member.getId()

    member_title = member.Title() or member_id
    folder = mtool.getHomeFolder(member_id)
    folder.setTitle(member_title)
    alsoProvides(folder, IMemberFolder)
    apply_member_folder_redirection(folder, request)

    page_id = "%s-home" % member_id
    title = "%s Home" % member_title
    folder.invokeFactory('Document', page_id, title=title)
    folder.setLayout('profile')

    page = getattr(folder, page_id)
    # XXX acquisition, ugh @@ huh?
    page_text = member.member_index(member_id=member_id)
    page.setText(page_text)

    # the page is the homepage
    alsoProvides(page, IMemberHomePage)

    # make profile the default view on the homepage
    page.setLayout('profile.html')



@adapter(IFirstLoginEvent)
def auto_approve_member(event):
    # if there is a parent project in the
    # request which implements IConsumeNewMembers,
    # automatically register the user as a member
    # of the project.
    request = event.request
    parent = get_parent_project(request)

    if parent is not None:
        team = parent.getTeams()[0]
        if team is not None: 
            team.joinAndApprove()

def get_parent_project(request):
    parents = request.get('PARENTS', tuple())

    for parent in parents:
        # check the request for a greedy project project,
        # ie one that is redirected and marked with IConsumeMembers
        if (redirect.IRedirected.providedBy(parent) and
            IConsumeNewMembers.providedBy(parent) and 
            IProject.providedBy(parent)):
            return parent

def apply_member_folder_redirection(folder, request):
    parent = get_parent_project(request) 
    if parent:
        parent_info = redirect.get_info(parent)
        folder_id = folder.getId()
        folder_path = parent_info.url
        if not folder_path.endswith('/'):
            folder_path += '/'
        #XXX not crazy about this assuming the folder is 'people'
        folder_path += "people/%s" % folder_id
        return redirect.activate(folder, url=folder_path)
    else:
        return redirect.activate(folder)



    

