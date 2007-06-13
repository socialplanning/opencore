"""
some base class for opencore ui work
"""
from Acquisition import aq_inner, aq_parent
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.utils import transaction_note
from Products.Five import BrowserView
from Products.OpenPlans.content.project import OpenProject
from Products.OpenPlans.interfaces import IReadWorkflowPolicySupport
from Products.remember.interfaces import IReMember
from opencore import redirect 
from opencore.content.member import OpenMember
from opencore.content.page import OpenPage
from opencore.interfaces import IProject 
from opencore.nui.static import render_static
from plone.memoize import instance
from plone.memoize import view 
from topp.featurelets.interfaces import IFeatureletSupporter
from topp.utils.pretty_date import prettyDate
from topp.utils.pretty_text import truncate
from zope.component import getMultiAdapter, adapts, adapter

# XXX these shouldn't be imported here -- they aren't used in this file
from opencore.nui.formhandler import button, post_only, anon_only, octopus

view.memoizedproperty = lambda func: property(view.memoize(func))
view.mcproperty = lambda func: property(view.memoize_contextless(func))


class BaseView(BrowserView):
    """Base view for general use for nui templates and as an abstract base"""
    logoURL = '++resource++img/logo.gif'
    defaultPortraitURL = '++resource++img/default-portrait.jpg'
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
    def member_info(self):
        """
        Returns a dict containing information about the currently
        authenticated member for easy template access.  If the member
        is not currently logged in, the returned dictionary will be
        empty.
        """
        return self.member_info_for_member(self.loggedinmember)

    @instance.memoizedproperty
    def viewed_member_info(self):
        """
        Returns a dict containing information about the currently
        viewed member for easy template access.
        """
        return self.member_info_for_member(self.viewedmember())

    def viewed_member_profile_tags(self, field):
        return self.member_profile_tags(self.viewedmember(), field)

    def member_profile_tags(self, member, field):
        """
        Returns a list of dicts mapping each tag in the given field of the
        given member's profile to a url corresponding to a search for that tag.
        """
        if IReMember.providedBy(member):
            tags = getattr(member, 'get%s' % field.title())()
            tags = tags.split(',')
            tagsearchurl = 'http://www.openplans.org/tagsearch/' # TODO
            urls = [tagsearchurl + tag for tag in tags]
            return [{'tag': tag, 'url': url} for tag, url in zip(tags, urls)]
        return []


    def member_info_for_member(self, member):
        if member is not None:
            if IReMember.providedBy(member):
                result = dict(
                              id          = member.getId(),
                              fullname    = member.getFullname(),
                              membersince = prettyDate(member.getRawCreation_date()),
                              lastlogin   = prettyDate(member.getLast_login_time()),
                              location    = member.getLocation(),
                              url         = '',
                             )
            else:
                # XXX TODO 
                # we're an old school member object, e.g. an admin user
                result = dict(id=member.id, fullname=member.fullname)

                for key in 'membersince', 'lastlogin','location', \
                           'statement', 'affiliations', 'skills', \
                           'background',  'url', 'favorites':
                    result[key] = ''

            folder = self.membertool.getHomeFolder(result['id'])
            if folder:
                result['url'] = folder.absolute_url()
                
            result['portrait_url'] = self.defaultPortraitURL
            portrait = member.getProperty('portrait', None)
            if portrait:
                result['portrait_url'] = portrait.absolute_url()

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

    def projectobj(self): # TODO
        return self.piv.project

    # properties and methods associated with members

    @property
    def loggedinmember(self):
        if self.loggedin:
            return self.membertool.getAuthenticatedMember()

    def home_url_for_id(self, id_=None):
        if id_ == None:
            return self.home_url
        return "%s/%s" %(self.membertool.getHomeFolder().absolute_url(), id_)

    @view.mcproperty
    def home_url(self):
        """url of the member's homepage"""
        if not self.loggedin:
            return None
        id_ = self.loggedinmember.getId()
        return self.home_url_for_id(id_)

    def userobj(self):
        # XXX eliminate
        return self.membertool.getAuthenticatedMember()

    @property
    def loggedin(self):
        return not self.membertool.isAnonymousUser()

    @view.memoize
    def viewedmember(self):
        """Returns the user found in the context's acquisition chain, if any."""
        return self.miv.member

    @view.memoizedproperty
    def inmember(self):
        return (self.miv.inMemberArea or self.miv.inMemberObject)

    # properties and methods associated with objects

    def inproject(self): # TODO
        return self.piv.inProject

    def projectFeaturelets(self):
        fletsupporter = IFeatureletSupporter(self.context)
        featurelet_ids = fletsupporter.getInstalledFeatureletIds()
        featurelets = [{'name': id, 'url' : fletsupporter.getFeatureletDescriptor(id)['content'][0]['id']} for id in featurelet_ids]
        return featurelets

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

    @instance.clearbefore
    def _clear_instance_memos(self):
        pass


def aq_iface(obj, iface):
    obj = aq_inner(obj)
    while obj is not None and not iface.providedBy(obj):
        obj = aq_parent(obj)
    return obj


def static_txt(fname):
    """module level cache?"""
    def new_func(self):
        return self.render_static(fname)
    return new_func

