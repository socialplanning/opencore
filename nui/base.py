"""
some base class for opencore ui work
"""
import datetime
from time import strptime
import urllib
import cgi
from Acquisition import aq_inner, aq_parent

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five import BrowserView

from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.utils import transaction_note
from Products.remember.interfaces import IReMember

from Products.OpenPlans.content.project import OpenProject
from Products.OpenPlans.interfaces import IReadWorkflowPolicySupport

from zope.component import getMultiAdapter, adapts, adapter

from plone.memoize import instance
from plone.memoize import view 

from topp.featurelets.interfaces import IFeatureletSupporter
from topp.utils.pretty_date import prettyDate
from topp.utils.pretty_text import truncate

from opencore import redirect 
from opencore.content.member import OpenMember
from opencore.content.page import OpenPage
from opencore.interfaces import IProject 
from opencore.nui.static import render_static

# XXX these shouldn't be imported here -- they aren't used in this file
# jeff, they are imported as a convenience api here 
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
    
    main_macros = ZopeTwoPageTemplateFile('main_macros.pt')

    def __init__(self, context, request):
        self.context      = context
        self.request      = request
        self.transcluded  = request.get_header('X-transcluded')
        self.errors = {}
        self.response = self.request.RESPONSE

    def redirect(self, *args, **kwargs):
        self._redirected = True
        return self.response.redirect(*args, **kwargs)

    def render_macro(self, macro, extra_context={}):
        """
        Returns a rendered page template which contains nothing but a
        provied macro.

        o macro: the macro list representation which should be
        rendered within the returned template object.
        """
        template = ZopeTwoPageTemplateFile('macro_snippet.pt').__of__(self)
        template._cook_check()
        extra_context['macro'] = macro
        return template.pt_render(extra_context=extra_context)

    @property
    def portal_status_message(self):
        if hasattr(self, '_redirected'):
            return []
        plone_utils = self.get_tool('plone_utils')
        msgs = plone_utils.showPortalMessages()
        if msgs:
            msgs = [msg.message for msg in msgs]
        else:
            msgs = []
        req_psm = self.request.form.get("portal_status_message")
        if req_psm:
            req_psm = cgi.escape(req_psm)
            msgs.append(req_psm)
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
        if self.inmember:
            return self.miv.member_folder
        elif self.piv.inProject:
            return self.piv.project
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
            tags = [tag.strip() for tag in tags if tag.strip()]
            tagsearchurl = 'http://www.openplans.org/tagsearch/' # TODO
            urls = [tagsearchurl + urllib.quote(tag) for tag in tags]
            return [{'tag': tag, 'url': url} for tag, url in zip(tags, urls)]
        return []


    def member_info_for_member(self, member):
        result = {}
        if IReMember.providedBy(member):
            id = member.getId()
            result.update(
                id          = id,
                fullname    = member.getFullname(),
                email       = member.getEmail(),
                membersince = prettyDate(member.getRawCreation_date()),
                lastlogin   = prettyDate(member.getLogin_time()),
                # TODO isloggedin = ???, # for e.g. 'online now' info in profile view
                folder_url  = self.memfolder_url(id_=id),
                home_url    = self.memhome_url(id_=id),
                projects    = member.projectBrains(),
                location    = member.getLocation(),
                statement   = member.getStatement(),
                background  = member.getBackground(),
                skills      = member.getSkills(),
                affiliations= member.getAffiliations(),
                favorites   = member.getFavorites(),
                anon_email  = member.getUseAnonByDefault(),
                )
        else:
            # XXX TODO 
            # we're an old school member object, e.g. an admin user
            result.update(id=member.id, fullname=member.fullname)

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
                             description=proj.Description(),
                             featurelets=self.piv.featurelets,
                             obj=proj)
        return proj_info

    # tool and view handling

    @view.memoize_contextless
    def get_tool(self, name):
        """
        Returns the specified tool.  Uses the context of the view as
        the context for the getToolByName call.
        """
        return getToolByName(self.context, name)

    def get_portal(self):
        return aq_iface(self.context, self.site_iface)

    portal = property(view.memoize_contextless(get_portal))

    @view.memoize
    def get_view(self, name):
        view = getMultiAdapter((self.context, self.request), name=name)
        return view.__of__(aq_inner(self.context))

    @property
    def piv(self):
        return self.get_view('project_info')

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

    @view.memoize
    def memfolder(self, id_=None):
        if id_ is None:
            if not self.loggedin:
                return None
            id_ = self.member_info['id']
        return self.membertool.getHomeFolder(id_)

    def memfolder_url(self, id_=None):
        """url of the given member's homepage.
        if none is specified, use logged-in member"""
        folder = self.memfolder(id_)
        if folder is not None:
            return folder.absolute_url()

    def memhome_url(self, id_=None):
        folder = self.memfolder(id_)
        if folder is not None:
            return '%s/%s' % (folder.absolute_url(),
                              folder.getDefaultPage())

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

    @property
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
    def memberdatatool(self):
        return self.get_tool('portal_memberdata')

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

    def pretty_date(self, date):
        try:
            time_obj = strptime(date, '%Y-%m-%d %H:%M:%S')
            datetime_obj = datetime.datetime(*time_obj[0:6])
        except TypeError:
            datetime_obj = date
        return prettyDate(datetime_obj)

    def get_tab_class(self, link):
        if not isinstance(link, list):
            link = [link]
        if self.name in link:
            return 'oc-selected'
        else:
            return ''

    def is_member(self, id):
        return self.memberdatatool.get(id) is not None

    def authenticator(self):
        return self.get_tool('browser_id_manager').getBrowserId(create=True)

    def authenticator_input(self):
        return '<input type="hidden" name="authenticator" value="%s" />' % self.authenticator()

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

