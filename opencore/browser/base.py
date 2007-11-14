"""
some base class for opencore ui work!
"""
from Acquisition import aq_inner, aq_parent
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.utils import transaction_note
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.remember.interfaces import IReMember
from opencore.interfaces import IProject 
from opencore.project.utils import project_path
from zope.i18nmessageid import Message
from opencore.i18n import i18n_domain, _
from opencore.i18n import translate
from plone.memoize import instance
from plone.memoize import view 
from time import strptime
from topp.featurelets.interfaces import IFeatureletSupporter
from topp.utils.pretty_date import prettyDate
from topp.utils.pretty_text import truncate
from zope.component import getMultiAdapter, adapts, adapter

import DateTime
import cgi
import datetime
import urllib

view.memoizedproperty = lambda func: property(view.memoize(func))
view.mcproperty = lambda func: property(view.memoize_contextless(func))


class BaseView(BrowserView):
    """Base view for general use for nui templates and as an abstract base"""
    logoURL = '++resource++img/logo.gif'
    defaultPortraitURL = '++resource++img/default-portrait.gif'
    defaultPortraitThumbURL = '++resource++img/default-portrait-thumb.gif'
    defaultProjLogoURL = '++resource++img/default-projlogo.gif'
    defaultProjLogoThumbURL = '++resource++img/default-projlogo-thumb.gif'
    windowTitleSeparator = ' :: '
    truncate = staticmethod(truncate)
    txn_note = staticmethod(transaction_note)
    site_iface = IPloneSiteRoot
    getToolByName=getToolByName

    def debug(self):
        """@@ this should be calculated from conf"""
        return True

    # XXX only used by formlite in this fashion
    main_macros = ZopeTwoPageTemplateFile('main_macros.pt')

    # XXX only used once, move into member/view
    _url_for = dict(projects="projects", project_create="projects/create",
                    login="login", forgot="forgot", join="join")
    def url_for(self, screen):
        return '%s/%s' % (self.siteURL, self._url_for[screen])

    def __init__(self, context, request):
        self.context      = context
        self.request      = request
        self.transcluded  = request.get_header('X-transcluded')
        self.errors = {}
        self.response = self.request.RESPONSE

    def redirect(self, *args, **kwargs):
        self._redirected = True
        return self.response.redirect(*args, **kwargs)

    def spamProtect(self, mailaddress, mailname=None):
        """
        Returns a spam protected mail address tag.  Lifted from the
        Plone skin script of the same name.
        """
        email = mailaddress.replace('@', '&#0064;').replace(':', '&#0058;')
        if mailname is None:
            mailname = email
        return '<a href="&#0109;ailto&#0058;' + email + '">' + mailname + '</a>'

    #XXX only used once, move into project.view
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

    def translate(self, msgid, domain=i18n_domain, mapping=None,
                  target_language=None, default=None):
        """
        Wrapper around translate machinery which defaults to our i18n
        domain and the current context object.  Returns instance of
        unicode type.
        """
        context = aq_inner(self.context)
        kw = dict(domain=domain, mapping=mapping, context=context,
                  target_language=target_language, default=default)
        return translate(msgid, **kw)

    @property
    def portal_status_message(self):
        # Note, showPortalMessages returns AND CLEARS them.
        # Hence this oddity: we don't want to clear them
        # if this view is redirecting, because then nobody would
        # ever see them.
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

    # XXX standardize
    def add_status_message(self, msg):
        plone_utils = self.get_tool('plone_utils')

        # portal messages don't seem to get translated implicitly
        # this is why there's an explicit translate here
        if isinstance(msg, Message):
            msg = self.translate(msg)
        else:
            msg = _(msg)

        plone_utils.addPortalMessage(msg)

    addPortalStatusMessage = add_status_message

    # XXX not used
    def include(self, viewname):
        if self.transcluded:
            return self.renderTranscluderLink(viewname)
        return self.get_view(viewname)()
    
    @view.memoizedproperty
    def area(self):
        if self.inmember:
            return self.miv.member_folder
        elif self.piv.inProject:
            return self.piv.project
        else:
            return self.portal

    # XXX only used in topnav
    @instance.memoizedproperty
    def areaURL(self):
        return self.area.absolute_url()

    # XXX cache more rigorously
    @view.memoize_contextless
    def nusers(self): 
        """Returns the number of users of the site."""
        users = self.membranetool(getId='')
        return len(users)

    # XXX cache more rigorously
    @view.memoize_contextless
    def projects_served_count(self): 
        """
        Returns the total number of projects hosted by the site,
        including those not visible to the current user.
        """
        projects = self.catalogtool.unrestrictedSearchResults(portal_type='OpenProject')
        return len(projects)

    @property
    def member_info(self):
        """
        Returns a dict containing information about the currently
        authenticated member for easy template access.  If the member
        is not currently logged in, the returned dictionary will be
        empty.
        """
        return self.member_info_for_member(self.loggedinmember)

    # XXX move to member.view
    @instance.memoizedproperty
    def viewed_member_info(self):
        """
        Returns a dict containing information about the currently
        viewed member for easy template access.
        """
        return self.member_info_for_member(self.viewedmember())

    # XXX move to member.view
    def viewed_member_profile_tags(self, field):
        return self.member_profile_tags(self.viewedmember(), field)

    # XXX move to member.view
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

    def mship_brains_for(self, member):
        teamtool = getToolByName(self.context, 'portal_teams')
        default_states = teamtool.getDefaultActiveStates()
        return self.catalog(id=member.getId(),
                            portal_type='OpenMembership',
                            review_state=default_states)

    def project_brains_for(self, member):
        if not IReMember.providedBy(member):
            return []
        mships = self.mship_brains_for(member)
        teams = [i.getPath().split('/')[-2] for i in mships]
        projects = self.catalog(portal_type='OpenProject', id=teams)
        return sorted(projects, key=lambda b:b.getId.lower())

    def project_brains(self):
        return self.project_brains_for(self.loggedinmember)

    def mship_proj_map(self):
        """map from team/project id's to {'mship': mship brain, 'proj': project brain}
        maps. relies on the 1-to-1 mapping of team ids and project ids."""
        mships = self.mship_brains_for(self.viewedmember())
        mp_map = {}
        for mship in mships:
            team = mship.getPath().split('/')[-2]
            mp_map[team] = dict(mship=mship)

        projects = self.project_brains_for(self.viewedmember())
        for proj in projects:
            mp_map[proj.getId]['proj'] = proj

        # XXX
        # the mship and the corresponding project should have the same visibility
        # permissions, such that the two queries yield len(projects) == len(mships).
        # there could be a discrepancy, however (caused by not putting placeful
        # workflow on the teams). the following will filter out items in the map
        # for which the logged in member cannot view both the mship and the corresponding
        # project of the viewed member.
        mp_copy = dict(mp_map)
        for (k, v) in mp_copy.items():
            if not v.has_key('proj'):
                del mp_map[k]

        return mp_map


    def member_info_for_member(self, member):
        if member == None:
            # Not logged in.
            return {}
        result = {}
        if IReMember.providedBy(member):
            id = member.getId()

            logintime = member.getLogin_time()
            if logintime == DateTime.DateTime('2000/01/01'): # XXX hack around zope
                logintime = 'never'
            else:
                logintime = logintime and prettyDate(logintime) or 'member.getLogin_time() is None?'
            
            result.update(
                id          = id,
                fullname    = member.getFullname(),
                email       = member.getEmail(),
                membersince = prettyDate(member.creation_date),
                lastlogin   = logintime,
                folder_url  = self.memfolder_url(id_=id),
                home_url    = self.memhome_url(id_=id),
                projects    = self.project_brains_for(member),
                location    = member.getLocation(),
                statement   = member.getStatement(),
                background  = member.getBackground(),
                skills      = member.getSkills(),
                affiliations= member.getAffiliations(),
                website     = member.getWebsite(),
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
            result['portrait_thumb_url'] = "%s_thumb" %portrait.absolute_url()
            result['portrait_width'] = str(portrait.width)
        else:
            result['portrait_thumb_url'] = self.defaultPortraitThumbURL
            result['portrait_width'] = '200' # XXX don't hard code width of default portrait

        return result

    @view.mcproperty
    def project_info(self):
        """
        Returns a dict containing information about the
        currently-viewed project for easy template access.

        calculated once
        """
        from opencore.interfaces.workflow import IReadWorkflowPolicySupport
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

    # XXX move to project view
    def get_portal(self):
        return aq_iface(self.context, self.site_iface)

    def portal_title(self):
        return self.portal.Title()
    
    portal = property(view.memoize_contextless(get_portal))

    # XXX move to topnav
    @view.memoize
    def get_view(self, name):
        view = getMultiAdapter((self.context, self.request), name=name)
        return view.__of__(aq_inner(self.context))

    #egj: piv? miv? these names suck.
    @property
    def piv(self):
        return self.get_view('project_info')

    @property
    def miv(self):
        return self.get_view('member_info')

    # XXX move to main.search
    @property
    def dob_datetime(self):
        return self.portal.created()

    # XXX move to main.search
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

    # remove (should be part of a form base class)
    def handle_request(self):
        raise NotImplementedError

    # XXX remove unused
    @staticmethod
    def renderTranscluderLink(viewname):
        return '<a href="@@%s" rel="include">%s</a>\n' % (viewname, viewname)

    # XXX remove, unused
    def projectobj(self): # TODO
        return self.piv.project

    # properties and methods associated with members

    @property
    def loggedinmember(self):
        if self.loggedin:
            return self.membertool.getAuthenticatedMember()

    # XXX move to topnav
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

    @property
    def loggedin(self):
        return not self.membertool.isAnonymousUser()

    #egj: this feels very convoluted, do we need to do it this way?
    # XXX move to member.view
    @view.memoize
    def viewedmember(self):
        """Returns the user found in the context's acquisition chain, if any."""
        return self.miv.member

    @view.memoizedproperty
    def inmember(self):
        return (self.miv.inMemberArea or self.miv.inMemberObject)

    # properties and methods associated with objects

    # XXX move to topnav
    @property
    def inproject(self): # TODO
        return self.piv.inProject

    # unused??
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

    @property
    def projects_url(self, project=None):
        return '%s/%s' % ( self.siteURL, project_path(project) )

    @instance.clearbefore
    def _clear_instance_memos(self):
        pass

    def pretty_date(self, date):
        return prettyDate(date)

    def get_tab_class(self, link):
        css_class = ''
        if not isinstance(link, list):
            link = [link]

        if self.name in link:
            css_class = 'oc-selected'

        if u'edit' in link:
            if not self.get_tool("portal_membership").checkPermission("Modify portal content", self.context):
                css_class = 'oc-notallowed'

        return css_class
    

    def is_member(self, id):
        return self.memberdatatool.get(id) is not None

    # XXX move to a form base class
    def authenticator(self):
        return self.get_tool('browser_id_manager').getBrowserId(create=True)

    # XXX move to a form base class
    def authenticator_input(self):
        return '<input type="hidden" name="authenticator" value="%s" />' % self.authenticator()

    # XXX move to a form base class
    def validate_password_form(self, password, password2, member):

        messages = []
        def exit_function():
            """bridge code to going forward. use this instead of return"""
            # XXX ultimately validate_password_form should play more nicely with messages
            if messages:
                for msg in messages:
                    self.addPortalStatusMessage(msg)
                return False
            return member

        if isinstance(member, basestring):
            # get the member object
            id = member
            if not id:
                messages.append(_(u'password_no_username_error', u'You need to enter your username.'))
                return exit_function()
                
            member = self.get_tool("membrane_tool")(getUserName=id)
            if not member:
                messages.append(_(u'password_no_member_error', u'There is no member named "${user_id}".',
                                  mapping={u'user_id':id}))
                return exit_function()
            member = member[0].getObject()

        if not password or not password2:
            messages.append(_(u'password_no_password_error', u"You must enter a password."))
            return exit_function()
        if password != password2:
            messages.append(_(u'password_not_same_error', u"Please make sure that both password fields are the same."))
            return exit_function()
        msg = member.validate_password(password)
        if msg:
            messages.append(msg)
            return exit_function()
        return exit_function() # XXX redundant, leaving for now

    def render_base_tag(self):
        """return the html that main template uses to fix relative links

        turning it off in the base template conditionally fails
        because the tal doesn't get rendered"""
        base_url = self.context.absolute_url()
        return """\
                <!--[if IE 6]><![if !IE 6]><![endif]-->
        <base href="%s/" />
                <!--[if IE 6]><![endif]><![endif]-->""" % base_url

try:
    from topp.utils import zutils
    aq_iface = zutils.aq_iface
except ImportError:
    def aq_iface(obj, iface):
        obj = aq_inner(obj)
        while obj is not None and not iface.providedBy(obj):
            obj = aq_parent(obj)
        return obj
