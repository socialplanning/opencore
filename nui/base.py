"""
some base class for opencore ui work
"""
from Acquisition import aq_inner, aq_parent
from opencore.content.page import OpenPage
from opencore.content.member import OpenMember
from Products.OpenPlans.content.project import OpenProject
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from plone.memoize import instance
from plone.memoize import view 
from opencore import redirect 
from opencore.interfaces import IProject 
from zope.component import getMultiAdapter, adapts, adapter
from topp.utils.pretty_text import truncate
from topp.utils.pretty_date import prettyDate
from opencore.nui.static import render_static
from topp.featurelets.interfaces import IFeatureletSupporter
from Products.OpenPlans.interfaces import IReadWorkflowPolicySupport
from zope.component import getMultiAdapter, adapts, adapter
from Products.CMFPlone import transaction_note


view.memoizedproperty = lambda func: property(view.memoize(func))
view.mcproperty = lambda func: property(view.memoize_contextless(func))

class BaseView(BrowserView):
    """Base view for general use for nui templates and as an abstract base"""
    logoURL = '++resource++img/logo.gif'
    windowTitleSeparator = ' :: '
    render_static = staticmethod(render_static)
    txn_note = staticmethod(transaction_note)
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
        plone_utils = getToolByName(self.context, 'plone_utils')
        msgs = plone_utils.showPortalMessages()
        msgs = [msg.message for msg in msgs]
        return msgs

    def addPortalStatusMessage(self, msg):
        plone_utils = self.get_tool('plone_utils')
        # @@ can we toplevel this import?
        from Products.CMFPlone import PloneMessageFactory
        plone_utils.addPortalMessage(PloneMessageFactory(msg))

    def include(self, viewname):
        if self.transcluded:
            return self.renderTranscluderLink(viewname)
        return self.get_view(viewname)()

    @view.memoizedproperty
    def loggedin(self):
        return not self.membertool.isAnonymousUser()

    @view.memoize
    def vieweduser(self): # TODO
        """Returns the user found in the context's acquisition chain, if any."""
        return self.miv.member

    @view.memoizedproperty
    def inmember(self):
        return (self.miv.inMemberArea or self.miv.inMemberObject)

    # XXX these two approach has different results
    # which is correct???
    def pagetitle(self):
        if self.inproject():
            return self.currentProjectPage().title
        return self.context.title # TODO?

    @property
    def pagetitle(self):
        return self.context.Title()

    
    @view.memoizedproperty
    def areatitle(self):
        # these require aq walks. might make more sense to have a
        # traversal hook stash the info on/in the request.
        title = ''
        if self.piv.inProject:
            title = self.piv.project.getFull_name()
        elif self.inmember:
            title = self.miv.member.getFullname()
        return title

    @instance.memoize
    def windowtitle(self):
        pagetitle, areatitle = truncate(self.pagetitle, max=24), \
                               truncate(self.areatitle, max=16)
        titles = [pagetitle, areatitle, self.sitetitle]
        return self.windowTitleSeparator.join([i for i in titles if i])

    @instance.memoizedproperty
    def areaURL(self):
        if self.piv.inProject:
            return self.piv.project.absolute_url()
        if self.inmember:
            return self.miv.member.absolute_url()
        else: # TODO
            return ''

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
            url = self.membertool.getHomeFolder(id).absolute_url()

            result.update(id=id, fullname=fullname, lastlogin=lastlogin,
                          url=url)
        return result

    @instance.memoizedproperty
    def project_info(self):
        """
        Returns a dict containing information about the
        currently-viewed proj`ect for easy template access.
        """
        proj_info = {}
        if self.piv.inProject:
            proj = self.piv.project
            proj_info.update(navname=proj.Title(),
                             fullname=proj.getFull_name(),
                             url=proj.absolute_url(),
                             mission=proj.Description(),
                             featurelets=self.piv.featurelets)
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
        wrapped = self.__of__(aq_inner(self.context))
        return wrapped.getToolByName(name)

    def get_portal(self):
        return self.portal_url.getPortalObject()

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
        return str(self.portal_url())

    @property
    def sitetitle(self):
        return self.get_portal().Title()

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
            security = IReadWorkflowPolicySupport(proj).getCurrentPolicyId()
            return dict(navname=proj.getId(),
                        fullname=proj.getFull_name(),
                        url=proj.absolute_url(), # XXX use self.projectHomePage.absolute_url() instead?
                        home=self.projectHomePage(),
                        mission=proj.Description(),
                        security=security,
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


# topnav drek #
##     def magicTopnavSubcontext(self): # TODO get rid of magic inference
##         if self.inproject():
##             return 'oc-topnav-subcontext-project'
##         elif self.inuser():
##             return 'oc-topnav-subcontext-user'
##         return 'oc-blank'

##     def magicContent(self): # TODO get rid of magic inference
##         if self.inproject():
##             return 'oc-project-view'
##         elif self.inuser():
##             return 'oc-user-profile'
##         return 'oc-blank'

##     def renderTopnavSubcontext(self, viewname):
##         viewname = viewname or self.magicTopnavSubcontext()
##         return self.renderView(self.get_view(viewname))


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
