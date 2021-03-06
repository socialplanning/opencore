"""
some base class for opencore ui work!
"""
from Acquisition import aq_inner, aq_chain
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.remember.interfaces import IReMember
from lxml.html.clean import Cleaner
from opencore.browser.window_title import window_title
from opencore.i18n import i18n_domain, _
from opencore.i18n import translate
from opencore.utility.interfaces import IProvideSiteConfig
from opencore.interfaces import IHomePage
from opencore.project.utils import project_noun
from opencore.utils import timestamp_memoize
from plone.memoize import instance
from plone.memoize import view
from topp.utils import zutils
from topp.utils.pretty_date import prettyDate
from zope.component import getMultiAdapter, getUtility
from zope.i18nmessageid import Message
import DateTime
import cgi
import logging

try:
    from opencore.streetswiki.interfaces import IWikiContainer
except ImportError:
    IWikiContainer = None

view.memoizedproperty = lambda func: property(view.memoize(func))
view.mcproperty = lambda func: property(view.memoize_contextless(func))
logger = logging.getLogger("opencore.browser.base")

class BaseView(BrowserView):
    """Base view for general use for nui templates and as an abstract base"""

    # @@ DWM: following should go in configuration
    logoURL = '++resource++img/logo.gif'
    defaultPortraitURL = '++resource++img/default-portrait.gif'
    defaultPortraitThumbURL = '++resource++img/default-portrait-thumb.gif'
    defaultPortraitSquareThumbURL = '++resource++img/default-portrait-80x80.gif'
    defaultPortraitSquareFiftyThumbURL = '++resource++img/default-portrait-50x50.gif'
    defaultProjLogoURL = '++resource++img/default-projlogo.gif'
    defaultProjLogoThumbURL = '++resource++img/default-projlogo-thumb.gif'
    windowTitleSeparator = ' :: '
    site_iface = IPloneSiteRoot

    main_macros = ZopeTwoPageTemplateFile('main_macros.pt')

    def __init__(self, context, request):
        self.context      = context
        self.request      = request
        self.transcluded  = request.get_header('X-transcluded')
        self.errors = {}
        self.response = self.request.RESPONSE
    
    def get_config(self, option, default=''):
        # XXX As of 5/20/08 only Sputnik templates use this method,
        # but I don't feel like doing the work to move it elsewhere,
        # because sputnik often uses views that derive from this class
        # and not from anything sputnik-specific ... so there's no
        # existing class that's a good place to put it.
        return getUtility(IProvideSiteConfig).get(option, default=default)

    def project_url(self, project=None, page=None, path=False):
        """This should be the canonical way for views to get a url
        related to projects.  Returns an absolute URL.

        o project: id of the project for which you want the URL.  If
          None, then the URL of the projects folder will be returned.

        o page: id of a page within the project.  If provided, the URL
          for the page is returned instead of the project's URL.  If
          project is None, will be relative to the container of
          projects.

        o path: if True, then the absolute physical path will be
          returned instead of the URL.
        """
        #XXX hardcoded 'projects' folder id :P
        pfolder = self.portal.projects
        if path:
            prefix = '/'.join(pfolder.getPhysicalPath())
        else:
            prefix = pfolder.absolute_url()
        parts = [prefix]
        if project is not None:
            parts.append(project)
        if page is not None:
            parts.append(page)
        return '/'.join(parts)

    @property
    def project_noun(self):
        """Do we call them 'projects' or 'groups' or... ?
        """
        return project_noun()

    def redirect(self, *args, **kwargs):
        self._redirected = True
        return self.request.response.redirect(*args, **kwargs)

    def spamProtect(self, mailaddress, mailname=None):
        """
        Returns a spam protected mail address tag.  Lifted from the
        Plone skin script of the same name.
        """
        email = mailaddress.replace('@', '&#0064;').replace(':', '&#0058;')
        if mailname is None:
            mailname = email
        return '<a href="&#0109;ailto&#0058;' + email + '">' + mailname + '</a>'

    def render_macro(self, macro, extra_context={}):
        """
        Returns a rendered page template which contains nothing but a
        provided macro.

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
        # @@ consider moving to a function
        
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

    # XXX standardize the method name
    def add_status_message(self, msg):
        # Allow the user to pass in either msg id strings or messages.
        if isinstance(msg, basestring) and not isinstance(msg, Message):
            msg = _(msg)
        assert isinstance(msg, Message)
        # Need to explicitly translate now because the cleaner needs
        # to be passed text, not a msg. plone_utils *could* translate
        # the message automatically if we didn't do the cleaning.
        msg = self.translate(msg)
        cleaner = Cleaner()
        msg = cleaner.clean_html(msg)
        if msg.startswith('<p>'):
            msg = msg[3:-4]
        msg = unicode(msg)
        plone_utils = self.get_tool('plone_utils')
        plone_utils.addPortalMessage(msg, request=self.request)

    addPortalStatusMessage = add_status_message

    @view.memoizedproperty
    def wiki_container(self):
        """
        Check aq_chain for IWikiContainer objects, return if exists.
        """
        if IWikiContainer is None: # streetswiki isn't installed
            return
        chain = aq_chain(aq_inner(self.context))
        for item in chain:
            if IWikiContainer.providedBy(item):
                return item

    # this should be put in a viewlet in an oc-twirlip plugin -egj
    def twirlip_uri(self):
        site_url = getToolByName(self.context, 'portal_url')()
        if site_url[-1] == "/":
            site_url = site_url[:-1]
        path = getUtility(IProvideSiteConfig).get("twirlip path", '')
        return site_url + path.strip()

    @view.memoizedproperty
    def area(self):
        """
        Adapt the current view to an `area` of the site, with a dict-like
        interface to the following metadata about the current site area:
         * Title: The unicode representation of a human-readable display title for the area.
         * absolute_url:  The URL path to the area.
         * homepage_url:  The URL that the area considers to be its "home page"/default view.
                          If the area prefers to have no "home page", it can return None here.
         * verbose_title: A base string that can be used to construct a window title (ie html <TITLE>).
                          This verbose_title is sort of like an overridable breadcrumb trail.
                          It's used in the `window_title` method of this same class; the docstring
                          there is probably the best way to understand what this is supposed to be.
        A site area may represent any of the following:
         * a member area, if the current view is under the member folder or member object
         * a project area, if the current view is under the project container
         * a wiki area, if the current view is under a wiki container (no such implementations
           in opencore itself, but see StreetsWiki for an example)
         * the site portal / site root itself, otherwise

        We may want to consider making this list extensible by third parties; for instance, 
        Dimo's http://indy.gr has sitewide containers for user-contributed discussions, media,
        wiki pages, etc, which might conceivably benefit from this interface. It also sounds
        like NYCStreets might have benefited from making individual cases easily overridable
        """
        if self.miv.inMemberArea or self.miv.inMemberObject:
            member = self.miv.member
            if member is not None:
                info = self.member_info_for_member(self.miv.member)
                title = info['Title'].decode('utf-8')
                verbose_title = _(u'member_area_verbose_title',
                                  u'${title} on ${portal_title}',
                                  mapping={u'title': title,
                                           u'portal_title': self.portal_title(),
                                           }
                                  )
                return {
                    'Title': title,
                    'homepage_url': info['absolute_url'] + '/%s-home' % info['id'],
                    'absolute_url': info['absolute_url'],
                    'verbose_title': self.translate(verbose_title)
                    }

        elif self.piv.inProject:
            info = self.piv.project
            title = info.Title().decode('utf-8')
            verbose_title = _(u'project_area_verbose_title',
                              u'${title} - ${portal_title}',
                              mapping={u'title': title,
                                       u'portal_title': self.portal_title(),
                                       }
                              )
            return {
                'Title': title,
                'homepage_url': info.absolute_url() + '/' + IHomePage(info).home_page,
                'absolute_url': info.absolute_url(),
                'verbose_title': self.translate(verbose_title)
                }

        elif self.wiki_container is not None:
            info = self.wiki_container
            title = info.Title().decode('utf-8')
            verbose_title = _(u'wiki_area_verbose_title',
                              u'${title} - ${portal_title}',
                              mapping={u'title': title,
                                       u'portal_title': self.portal_title(),
                                       }
                              )
            return {
                'Title': title,
                'homepage_url': None, # wiki containers do not have a homepage_url
                'absolute_url': info.absolute_url(),
                'verbose_title': self.translate(verbose_title)
                }

        # default case is the portal itself
        # this includes an edge case that i believe only exists in the member-delete
        # view when the member object has been deleted but the member area hasn't yet
        info = self.portal
        title = info.Title().decode('utf-8')
        verbose_title = _(u'portal_area_verbose_title',
                          u'${title}',
                          mapping={u'title': title,
                                   u'portal_title': self.portal_title(),
                                   }
                          )
        return {
            'Title': title,
            'homepage_url': info.absolute_url(),
            'absolute_url': info.absolute_url(),
            'verbose_title': self.translate(verbose_title)
            }

    def window_title(self, mode=None):
        """
        mode should be one of: 'view', 'edit', or 'history'.

        Basically this generates a window title that is a breadcrumb list
        of the hierarchy of major "site areas" that contain the current
        view's context object.  For example:

         * OpenPlans
           # /openplans
         * Our New Project - OpenPlans
           # /openplans/projects/ourproject
         * My Wiki Home - Eddie McPherson - OpenPlans
           # /openplans/people/eddie/eddie-home

        If the current view is an "interesting" view on the context, the
        name of the view (passed in as the `mode` string) will be displayed
        as well, like:

         * My Wiki Home (history) - Eddie McPherson on OpenPlans
           # /openplans/people/eddie/eddie-home/history

        The first set of examples above is actually incorrect, though, because
        the breadcrumbs displayed aren't required to implement a strict traversal
        hierarchy -- see http://trac.openplans.org/openplans/ticket/588#comment:5
        Instead, the `area` object is trusted to provide its own "breadcrumb
        trail" (provided as `area['verbose_title']`) which is then combined with
        the "current breadcrumb" component of the view itself. So:

        * Our New Project
          # /openplans/projects/ourproject
          # ...project areas are "all about the project itself" so they do not
          #    display the portal-level breadcrumb

        * Project Home (edit) - Our New Project
          # /openplans/project/ourproject/project-home/edit

        * My Wiki Home - Eddit McPherson on OpenPlans
          # /openplans/people/eddie/eddie-home
          # ...member areas choose to display the portal-level breadcrumb, but
          #    they use the friendlier-sounding preposition  "on" rather than
          #    the otherwise uniform separator "-"

        Phew!

        It also includes logic to deal with "area home pages".  For example, visiting
        the URL /openplans/projects/myproject/lists will normally produce a window
        title of "Lists - Our New Project", but if the project's
        homepage is set to "Mailing Lists" it will instead be displayed as
        "Our New Project".
        """
        area = self.area

        return window_title(area, self.context.absolute_url(),
                            self.context.Title().decode('utf-8'),
                            mode)



    @timestamp_memoize(600)
    def nusers(self): 
        """Returns the number of users of the site."""
        users = self.membranetool(meta_type='OpenMember')
        return len(users)

    @timestamp_memoize(600)
    def projects_served_count(self): 
        """
        Returns the total number of projects hosted by the site,
        including those not visible to the current user.
        """
        projects = self.catalog.unrestrictedSearchResults(portal_type='OpenProject')
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

    @instance.memoizedproperty
    def viewed_member_info(self):
        """
        Returns a dict containing information about the currently
        viewed member for easy template access.
        """
        return self.member_info_for_member(self.viewedmember())

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

    def member_info_for_member(self, member):
        if member == None:
            # Not logged in.
            return {}
        id = member.getId()
        result = {'id': id}
        folder = self.membertool.getHomeFolder(id)
        if folder:
            # we only add a URL to the result dict if the member folder exists.
            # if the folder does not exist, that means that the member has never
            # logged in (since member folders are created on first login, after
            # account confirmation)
            # if the folder does not exist, we have no good link to the member
            # so we just don't provide one
            result['url'] = folder.absolute_url()
            result['absolute_url'] = folder.absolute_url()

        if IReMember.providedBy(member):
            logintime = member.getLogin_time()
            if logintime == DateTime.DateTime('2000/01/01'): # XXX hack around zope
                logintime = 'never'
            else:
                logintime = logintime and prettyDate(logintime) or 'member.getLogin_time() is None?'
            
            result.update(
                id          = id,
                Title       = member.Title(),
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
            result.update(fullname=member.fullname)

            for key in 'membersince', 'lastlogin','location', \
                    'statement', 'affiliations', 'skills', \
                    'background',  'url', 'favorites', 'folder_url':
                result[key] = ''

        folder = self.membertool.getHomeFolder(result['id'])
        if folder:
            result['url'] = folder.absolute_url()

        # @@ DWM: should be in an adapter or on the member object
        result['portrait_url'] = self.defaultPortraitURL
        portrait = member.getProperty('portrait', None)
        if portrait:
            result['portrait_url'] = portrait.absolute_url()
            result['portrait_thumb_url'] = "%s_thumb" %portrait.absolute_url()
            result['portrait_width'] = str(portrait.width)
        else:
            result['portrait_thumb_url'] = self.defaultPortraitThumbURL
            result['portrait_width'] = '200' # XXX don't hard code width of default portrait

        # XXX We should do something like the following to avoid
        # potential UnicodeDecodeErrors all over the place; But lots
        # of tests are wired to expect str output and I don't have
        # time to chase those down and decide if I'm right.  - Paul W.
#         for key, val in result.items():
#             # Much of this came from archetypes data, which
#             # horrifically stores everything as encoded bytes...decode
#             # it to be safe.
#             if isinstance(val, str):
#                 try:
#                     result[key] = val.decode('utf-8')
#                 except UnicodeDecodeError:
#                     # XXX we have non-utf8 data? dunno what to do then.
#                     pass
        return result

    # tool and view handling

    # PW: I don't know what motivated caching tool lookups; I did some
    # quick timeit benchmarks and determined that this saves maybe
    # 0.00001 seconds per lookup, so I really doubt there will ever be
    # a bottleneck here.
    @view.memoize_contextless
    def get_tool(self, name):
        """
        Returns the specified tool.  Uses the context of the view as
        the context for the getToolByName call.
        """
        return getToolByName(self.context, name)

    @view.mcproperty
    def portal(self):
        return aq_iface(self.context, self.site_iface)

    def portal_title(self):
        return self.portal.Title().decode('utf8')
    
    #egj: piv? miv? these names suck.

    #pmw: even after memoization, we sometimes see piv called more
    #than once per request. Tried view.memoizedproperty, but that's
    #even worse.
    @instance.memoizedproperty
    def piv(self):
        view = getMultiAdapter((self.context, self.request), name='project_info')
        return view.__of__(aq_inner(self.context))

    @instance.memoizedproperty
    def miv(self):
        view = getMultiAdapter((self.context, self.request), name='member_info')
        return view.__of__(aq_inner(self.context))

    @property
    def dob(self):
        return prettyDate(self.portal.created())

    @property
    def came_from(self):
        # pw: as of 2008/04/14, not much uses this base class implementation,
        # but formhandler.anon_only requires all views to have it.
        came_from = self.request.get('came_from')
        return came_from or getToolByName(self.context, 'portal_url')()

    def admin_loggedin(self):
        return self.get_tool("portal_membership").checkPermission(
            "Modify portal content", self.context)

    @property
    def name(self):
        """The name this view is registered for. We sometimes use this
        for constructing a link to the current view (for
        eg. self-posting forms"""
        return self.__name__

    # This is only here for documentation purposes; a lot of our form
    # handlers have a handle_request implementation.  Should it be
    # defined on some interface instead?
    def handle_request(self):
        raise NotImplementedError

    # properties and methods associated with members

    @property
    def loggedinmember(self):
        if self.loggedin:
            # XXX This can sometimes lead to downstream confusion by
            # returning users who aren't full site members,
            # eg. in tests where we've called loginAsPortalOwner()
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
        if id_ is None:
            if not self.loggedin:
                return None
            id_ = self.member_info['id']
        folder = self.memfolder(id_)
        if folder is not None:
            return '%s/%s-home' % (folder.absolute_url(),
                                   id_)

    @property
    def loggedin(self):
        return not self.membertool.isAnonymousUser()

    @view.memoize
    def viewedmember(self):
        """Returns the user found in the context's acquisition chain, if any."""
        #egj: this feels very convoluted, do we need to do it this way?
        return self.miv.member


    # properties and methods associated with objects

    @property
    def membranetool(self):
        return self.get_tool('membrane_tool')
    
    @property
    def membertool(self):
        return self.get_tool('portal_membership')
    
    @property
    def catalog(self):
        return self.get_tool('portal_catalog')

    @instance.clearbefore
    def _clear_instance_memos(self):
        pass

    def pretty_date(self, date, include_time=False):
        return prettyDate(date, include_time)

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

    def render_base_tag(self):
        """return the html that main template uses to fix relative links

        turning it off in the base template conditionally fails
        because the tal doesn't get rendered"""
        base_url = self.context.absolute_url()
        return """\
                <!--[if IE 6]><![if !IE 6]><![endif]-->
        <base href="%s/" />
                <!--[if IE 6]><![endif]><![endif]-->""" % base_url


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

aq_iface = zutils.aq_iface

