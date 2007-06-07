"""
some base class for opencore ui work
"""
from Acquisition import aq_inner, aq_parent
from Products.Five import BrowserView
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import transaction_note
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.remember.interfaces import IReMember

from zope.component import getMultiAdapter, adapts, adapter
from zope.component import getMultiAdapter, adapts, adapter

from plone.memoize import instance
from plone.memoize import view 
view.memoizedproperty = lambda func: property(view.memoize(func))
view.mcproperty = lambda func: property(view.memoize_contextless(func))

from topp.utils.pretty_text import truncate
from topp.utils.pretty_date import prettyDate
from topp.featurelets.interfaces import IFeatureletSupporter

from Products.OpenPlans.content.project import OpenProject
from Products.OpenPlans.interfaces import IReadWorkflowPolicySupport

from opencore import redirect 
from opencore.interfaces import IProject 
from opencore.content.page import OpenPage
from opencore.content.member import OpenMember
from opencore.nui.static import render_static


class BaseView(BrowserView):
    """Base view for general use for nui templates and as an abstract base"""
    logoURL = '++resource++img/logo.gif'
    windowTitleSeparator = ' :: '
    render_static = staticmethod(render_static)
    truncate = staticmethod(truncate)
    txn_note = staticmethod(transaction_note)
    site_iface = IPloneSiteRoot
    getToolByName=getToolByName
    
    def __init__(self, context, request):
        self.context      = context
        self.request      = request
        self.transcluded  = request.get_header('X-transcluded')
        self.errors = {}
        self.response = self.request.RESPONSE
        self.redirect = self.response.redirect

    @property
    def portal_status_message(self):
        plone_utils = self.get_tool('plone_utils')
        msgs = plone_utils.showPortalMessages()
        msgs = [msg.message for msg in msgs]
        return msgs

    def addPortalStatusMessage(self, msg):
        plone_utils = self.get_tool('plone_utils')
        plone_utils.addPortalMessage(_(msg))

    # memoize
    def include(self, viewname):
        if self.transcluded:
            return self.renderTranscluderLink(viewname)
        return self.get_view(viewname)()

    @property
    def loggedin(self):
        return not self.membertool.isAnonymousUser()

    @view.memoize
    def vieweduser(self): # TODO
        """Returns the user found in the context's acquisition chain, if any."""
        return self.miv.member

    @view.memoizedproperty
    def inmember(self):
        return (self.miv.inMemberArea or self.miv.inMemberObject)

    @property
    def pagetitle(self):
        return self.context.Title()
    
    @view.memoizedproperty
    def area(self):
        if self.piv.inProject:
            return self.piv.project
        elif self.inmember:
            return self.miv.member_folder
        else:
            return self.portal

    @view.memoizedproperty
    def areatitle(self):
        # these require aq walks. might make more sense to have a
        # traversal hook stash the info on/in the request.
        return self.area.Title()

    #@instance.memoize
    def windowtitle(self):
        pagetitle = self.truncate(self.pagetitle, max=24)
        areatitle = self.truncate(self.areatitle, max=16)
        titles = [pagetitle, areatitle, self.sitetitle]
        return self.windowTitleSeparator.join([i for i in titles if i])

    @instance.memoizedproperty
    def areaURL(self):
        return self.area.absolute_url()

    @view.memoize_contextless
    def nusers(self): 
        """Returns the number of users of the site."""
        users = self.membranetool(getId='')
        return len(users)

    @view.memoize_contextless
    def nprojects(self): # TODO cache
        """Returns the number of projects hosted by the site."""
        projects = self.catalogtool(portal_type='OpenProject')
        return len(projects)

    @view.memoizedproperty
    def canedit(self):
        canedit = self.membertool.checkPermission(ModifyPortalContent,
                                                  self.context)
        return bool(canedit)

    @instance.memoizedproperty
    def mem_data_map(self):
        """
        Returns a dict containing information about the currently
        authenticated member for easy template access.  If the member
        is not currently logged in, the returned dictionary will be
        empty.
        """
        member = None
        if self.loggedin:
            member = self.membertool.getAuthenticatedMember()

        result = {}
        if member is not None:
            if IReMember.providedBy(member):
                id = member.getId()
                fullname=member.getFullname()
                lastlogin=member.getLast_login_time()
            else:
                # we're an old school member object, i.e. an admin
                # user
                id = member.id
                fullname = member.fullname
                lastlogin = member.last_login_time
                
            url = ''
            folder = self.membertool.getHomeFolder(id)
            if folder:
                url = folder.absolute_url()

            result.update(id=id, fullname=fullname, lastlogin=lastlogin,
                          url=url)
        return result

    @view.mcproperty
    def project_info(self):
        """
        Returns a dict containing information about the
        currently-viewed project for easy template access.

        calculated once
        """
        proj_info = {}
        if self.piv.inProject:
            proj = aq_inner(self.piv.project)
            security = IReadWorkflowPolicySupport(proj).getCurrentPolicyId()
            proj_info.update(navname=proj.Title(),
                             fullname=proj.getFull_name(),
                             title=proj.Title(),
                             security=security,
                             url=proj.absolute_url(),
                             mission=proj.Description(),
                             featurelets=self.piv.featurelets,
                             obj=proj)
        return proj_info

    def user_exists(self, username):
        users = self.membranetool(getId=username)
        return len(users) > 0

    def userExists(self):
        username = self.request.get("username")
        if username is not None:
            return self.user_exists(username)
        return False

    # end of rob's refactors

    # tool and view handling

    @view.memoize_contextless
    def get_tool(self, name):
        wrapped = self.__of__(aq_inner(self.portal))
        return wrapped.getToolByName(name)

    def get_portal(self):
        return aq_iface(self.context, self.site_iface)

    portal = property(view.memoize_contextless(get_portal))

    @view.memoize
    def get_view(self, name):
        view = getMultiAdapter((self.context, self.request), name=name)
        return view.__of__(aq_inner(self.context))

    @property
    def piv(self):
        return self.get_view('project_info').__of__(aq_inner(self.context))

    @property
    def miv(self):
        return self.get_view('member_info')

    # properties (formerly in __init__.py)

    @property
    def dob_datetime(self):
        return self.portal.created()

    @property
    def dob(self):
        return prettyDate(self.dob_datetime)

    @property
    def siteURL(self):
        return aq_inner(self.portal).absolute_url()

    @property
    def came_from(self):
        return self.request.get('came_from') or self.siteURL

    @property
    def sitetitle(self):
        return self.portal.Title()

    @property
    def name(self):
        return self.__name__

    def handle_request(self):
        raise NotImplementedError

    # formerly functions in nui

    @staticmethod
    def renderTranscluderLink(viewname):
        return '<a href="@@%s" rel="include">%s</a>\n' % (viewname, viewname)

    @staticmethod
    def renderOpenPage(page):
        return page.CookedBody()

    @staticmethod
    def renderView(view):
        # XXX do we really need this?
        return view()

    # stuff rob removed in his opencoreview

    def renderContent(self, viewname):
        viewname = viewname or self.magicContent()
        return self.renderView(self.get_view(viewname))

    def renderProjectContent(self):
        return self.renderOpenPage(self.currentProjectPage())

    def projectobj(self): # TODO
        return self.piv.project

    @property
    def current_user(self):
        if self.current_member:
            return self.current_member.getUser()

    @property
    def current_member(self):
        return self.membertool.getAuthenticatedMember()

    def home(self, member=None):
        """url of the member's homepage"""
        if member is None:
            if not self.loggedin: return None
            member = self.current_member.id
        retval = '/'.join((self.portal.absolute_url(), 'people', member))
        return retval

    def userobj(self):
        # XXX eliminate
        return self.membertool.getAuthenticatedMember()

    def inproject(self): # TODO
        return self.piv.inProject

    def vieweduser(self): # TODO
        """Returns the user found in the context's acquisition chain, if any."""
        return self.miv.member

    def pageURL(self):
        if self.inproject():
            return self.currentProjectPage().absolute_url()
        return self.context.absolute_url() # TODO?

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

    @property
    def membranetool(self):
        return self.get_tool('membrane_tool')
    
    @property
    def membertool(self):
        return self.get_tool('portal_membership')

    @property
    def catalog(self):
        return self.get_tool('portal_catalog')

    catalogtool = catalog

    @property
    def portal_url(self):
        return self.get_tool('portal_url')


def button(name=None):
    def curry(handle_request):
        def new_method(self):
            if self.request.get(name):
                return handle_request(self)
            return None
        return new_method
    return curry


def post_only(raise_=True):
    def inner_post_only(func):
        """usually wrapped by a button"""
        def new_method(self):
            if self.request.environ['REQUEST_METHOD'] == 'GET':
                if raise_:
                    raise Forbidden('GET is not allowed here')
                return
            return func(self)
        return new_method
    return inner_post_only


def aq_iface(obj, iface):
    obj = aq_inner(obj)
    while obj is not None and not iface.providedBy(obj):
        obj = aq_parent(obj)
    return obj


def anon_only(redirect_to=None):
    def inner_anon_only(func):
        def new_method(self, *args, **kw):
            redirect_path = redirect_to
            if not redirect_path:
                redirect_path = self.came_from
            if self.loggedin:
                return self.redirect(redirect_path)
            return func(self, *args, **kw)
        return new_method
    return inner_anon_only

