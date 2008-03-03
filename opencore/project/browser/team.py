from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.MailHost.MailHost import MailHostError
from Products.validation.validators.BaseValidators import EMAIL_RE
from opencore.account.login import LoginView
from opencore.browser import formhandler
from opencore.browser.base import _
from opencore.configuration import DEFAULT_ROLES
from opencore.content.membership import OpenMembership
from opencore.interfaces.event import ChangedTeamRolesEvent
from opencore.interfaces.membership import IEmailInvites
from opencore.interfaces.message import ITransientMessage
from opencore.nui.email_sender import EmailSender
from opencore.nui.main import SearchView
from opencore.nui.main.search import searchForPerson
from opencore.project.browser import mship_messages
from opencore.utility.interfaces import IEmailSender
from operator import attrgetter
from plone.memoize.instance import memoize, memoizedproperty
from plone.memoize.view import memoize as req_memoize
from plone.memoize.view import memoize_contextless
from topp.utils.detag import detag
from zope.component import getUtility
from zope.event import notify
from zope.i18nmessageid import Message
import itertools
import re
import urllib


class TeamRelatedView(SearchView):
    """
    Base class for views on the project that are actually related to
    the team and team memberships.
    """
    def __init__(self, context, request):
        SearchView.__init__(self, context, request)
        project = self.context
        teams = project.getTeams()
        assert len(teams) == 1, "%d teams. 1 expected" %len(teams)
        self.team = team = teams[0]
        self.team_path = '/'.join(team.getPhysicalPath())
        self.active_states = team.getActiveStates()


class RequestMembershipView(TeamRelatedView, formhandler.OctopoLite, LoginView):
    """
    View class to handle join project requests.
    """
    template = ZopeTwoPageTemplateFile('request-membership.pt')

    def __call__(self):
        """ if already member of project, redirect appropriately """
        # if already a part of the team, redirect to project home page
        if self.member_info.get('id') in self.team.getActiveMemberIds():
            self.add_status_message(_(u'team_already_project_member',
                                        u'You are already a member of this project.'))
            self.redirect('%s?came_from=%s' % (self.context.absolute_url(), self.request.ACTUAL_URL))
        return super(RequestMembershipView, self).__call__()

    def _login(self):
        id_ = self.request.form.get("__ac_name")
        if not id_:
            return False

        pw = self.request.form.get("__ac_password")

        pm = self.get_tool("portal_membership")
        member = pm.getMemberById(id_)
        if member and member.verifyCredentials(dict(login=id_, password=pw)):
            acl = self.get_tool("acl_users")
            auth = acl.credentials_signed_cookie_auth
            auth.updateCredentials(self.request, self.response, id_, None)
            return True
        return False

    # XXX get rid of this!
    def _sendmail_to_pendinguser(self, id, email, url):
        """ send a mail to a pending user """
        # TODO only send mail if in the pending workflow state
        mailhost_tool = self.get_tool("MailHost")

        message = _(u'email_to_pending_user',
                    mapping={u'user_name':id,
                             u'url':url,
                             u'portal_url':self.siteURL,
                             u'portal_title':self.portal_title()})
        
        sender = IEmailSender(self.portal)
        sender.sendMail(mto=email,
                        msg=message)

    # XXX get this outta here right away
    def _create(self):
        mdc = self.get_tool('portal_memberdata')
        mem = mdc._validation_member

        self.errors = {}
        
        self.errors = mem.validate(REQUEST=self.request,
                                   errors=self.errors,
                                   data=1, metadata=0)
        password = self.request.form.get('password')
        password2 = self.request.form.get('confirm_password')
        if not password and not password2:
            self.errors.update({'password': _(u'no_password', u'Please enter a password') })

        if self.errors:
            return self.errors

        # create a member in portal factory
        mdc = self.get_tool('portal_memberdata')
        pf = mdc.portal_factory

        #00 pythonscript call, move to fs code
        id_ = self.context.generateUniqueId('OpenMember')

        mem_folder = pf._getTempFolder('OpenMember')
        mem = mem_folder.restrictedTraverse('%s' % id_)

        # now we have mem, a temp member. create him for real.
        mem_id = self.request.form.get('id')
        mem = pf.doCreate(mem, mem_id)
        self.txn_note('Created %s with id %s in %s' % \
                      (mem.getTypeInfo().getId(),
                       mem_id,
                       self.context.absolute_url()))
        result = mem.processForm()
        from zope.app.event.objectevent import ObjectCreatedEvent
        notify(ObjectCreatedEvent(mem))
        mem.setUserConfirmationCode()

        code = mem.getUserConfirmationCode()
        url = "%s/confirm-account?key=%s" % (self.siteURL, code)

        self._sendmail_to_pendinguser(id=mem_id,
                                      email=self.request.get('email'),
                                      url=url)
        self.addPortalStatusMessage(_('psm_thankyou_for_joining',
                                      u'Thanks for joining ${portal_title}, ${mem_id}!\nA confirmation email has been sent to you with instructions on activating your account. After you have activated your account, your request to join the project will be sent to the project administrators.',
                                      mapping={u'mem_id':mem_id,
                                               u'portal_title':self.portal_title()}))
        return mdc._getOb(mem_id)

    @formhandler.action('request-membership')
    def request_membership(self, targets=None, fields=None):
        """
        Delegates to the team object and handles destination.
        """
        if self.login_pending_member(): return

        joined = False
        ac_name = self.request.form.get("__ac_name")
        id_ = self.request.form.get("id")
        if self.loggedin: 
            # PAS will kick in, request will be "logged in" if form's login snippet is filled out correctly
            # so the user might be really logged in, or might have provided valid credentials w/request
            from opencore.interfaces.pending_requests import IRequestMembership
            req_msg = self.request.form.get("request-message")
            joined = IRequestMembership(self.team).join(req_msg)
            self._login() # conditionally set cookie if valid credentials were provided
        elif id_: # trying to create a member
            # create member
            mem = self._create()
            if isinstance(mem, dict):
                # failure, so return the errors to be rendered
                return mem 
            from zope.component import getMultiAdapter
            from opencore.interfaces.pending_requests import IPendingRequests
            req_bucket = getMultiAdapter((mem, self.portal.projects), IPendingRequests)
            req_msg = self.request.form.get("request-message")
            req_bucket.addRequest(self.context.getId(), request_message=req_msg)
            self.template = None # don't render the form before the redirect
            self.redirect(self.context.absolute_url())
            return
        elif ac_name: # trying to login, but failed
            self.addPortalStatusMessage(_(u'psm_check_username_password', u'Please check your username and password. If you still have trouble, you can <a href="forgot">retrieve your sign in information</a>.'))
            return
        else:
            self.add_status_message(u"You must login or create an account")
            return

        if not joined:
            psmid = 'already_proj_member'
            self.add_status_message(_(u'team_already_proj_member', u'You are already a pending or active member of ${project_title}.',
                                      mapping={'project_title':self.context.Title()}))
            self.template = None # don't render the form before the redirect
            self.redirect(self.context.absolute_url())
            return

        self.add_status_message(_(u'team_proj_join_request_sent',
                                  u'Your request to join "${project_title}" has been sent to the project administrator(s).',
                                  mapping={'project_title':self.context.Title()}))
        self.template = None # don't render the form before the redirect
        self.redirect(self.context.absolute_url())


class ProjectTeamView(TeamRelatedView):
    
    admin_role = DEFAULT_ROLES[-1]

    def __init__(self, context, request):
        super(ProjectTeamView, self).__init__(context, request)
        results = None
    
    def __call__(self):
        # @@ why is this redirect here? DWM
        if self.get_tool('portal_membership').checkPermission('TeamSpace: Manage team memberships', self.context):
            self.redirect(self.context.absolute_url() + '/manage-team')
        else:
            return super(ProjectTeamView, self).__call__()
   
    @formhandler.button('sort')
    def handle_request(self):
        # this is what controls which sort method gets dispatched to
        # in the memberships property
        return 

    def handle_sort_membership_date(self):
        query = dict(portal_type='OpenMembership',
                 path=self.team_path,
                 review_state=self.active_states,
                 sort_on='made_active_date',
                 sort_order='descending',
                 )

        membership_brains = self.catalog(**query)
        # XXX for some reason, the descending sort is not working properly
        # seems to only want to be ascending
        # so let's just use python sort to sort the results ourselves
        membership_brains = sorted(
            membership_brains,
            key=attrgetter('made_active_date'),
            reverse=True)

        mem_ids = [b.getId for b in membership_brains]
        
        query = dict(portal_type='OpenMember',
                     getId=mem_ids,
                     )

        # @@ DRY
        member_brains = self.result = self.membranetool(**query)
        lookup_dict = dict((b.getId, b) for b in member_brains if b.getId)
        batch_dict = [lookup_dict.get(b.getId) for b in membership_brains if lookup_dict.has_key(b.getId)]
        return self._get_batch(batch_dict, self.request.get('b_start', 0))

    def handle_sort_location(self):
        query = dict(portal_type='OpenMembership',
                 path=self.team_path,
                 review_state=self.active_states,
                 )
        mem_brains = self.catalog(**query)
        mem_ids = [mem_brain.getId for mem_brain in mem_brains]
        query = dict(sort_on='sortableLocation',
                     getId=mem_ids,
                     )
        # XXX these are member brains, not membership brains
        results = self.membranetool(**query)
        # XXX sort manually here, because it doesn't look like the catalog
        # has the ability to sort on multiple fields
        def sort_location_then_name(x, y):
            xloc, yloc = x.getLocation.lower(), y.getLocation.lower()
            if xloc < yloc: return -1
            if yloc < xloc: return 1
            return cmp(x.getId.lower(), y.getId.lower())

        # @@ DRY
        self.results = sorted(results, cmp=sort_location_then_name)
        return self._get_batch(self.results, self.request.get('b_start', 0))

    def handle_sort_contributions(self):
        return self._get_batch([], self.request.get('b_start', 0))

    def handle_sort_default(self):
        query = dict(portal_type='OpenMembership',
                     path=self.team_path,
                     review_state=self.active_states,
                     )
        mem_brains = self.catalog(**query)

        ids = [b.getId for b in mem_brains]
        query = dict(portal_type='OpenMember',
                     getId=ids,
                     sort_on='getId',
                     )
        
        # @@ DRY
        self.results = self.membranetool(**query)
        return self._get_batch(self.results, self.request.get('b_start', 0))

    def memberships(self, sort_by=None):
        if sort_by is None:
            sort_by = self.sort_by
        try:
            sort_fn = getattr(self, 'handle_sort_%s' % sort_by)
            return sort_fn()
        except (TypeError, AttributeError):
            return self.handle_sort_default()
            
##     def projects_for_member(self, member):
##         # XXX these should be brains
##         projects = self._projects_for_member(member)
##         # only return max 10 results
##         return projects[:10]

##     def num_projects_for_member(self, member):
##         projects = self._projects_for_member(member)
##         return len(projects)

##     @memoize_contextless
##     def _projects_for_member(self, member):
##         return member.getProjects()

    def _membership_record(self, brain):
        mem_id = brain['getId']
        project = self.context
        project_id = project.getId()
        team = self.team
        membership = team._getOb(mem_id)

        contributions = 'XXX'
        activation = self.pretty_date(membership.made_active_date)
        modification = self.pretty_date(membership.ModificationDate())
        project_ids = brain.project_ids        
        return dict(activation=activation,
                    contributions=contributions,
                    email=brain.getEmail,
                    fullname=brain.getFullname,
                    id=mem_id,
                    location=brain.getLocation,
                    modification=modification,
                    portrait_thumb_url=brain.portrait_thumb_url,
                    project_ids = project_ids,                    
                    )
    
    def _project_info(self, mem_brains):
        """
        concatenates a series of project ids for a collection of
        member brains and looks up the project brains
        """
        proj_ids = set(itertools.chain(*[sorted(brain.project_ids)[:10] for brain in mem_brains]))

        # @@ DWM: matching on id not as good as matching on UID
        pbrains = self.get_tool('portal_catalog')(getId=list(proj_ids), portal_type='OpenProject')
        return dict([(b.getId, b) for b in pbrains])

    @memoizedproperty
    def project_info(self):
        return self._project_info(self.results)

    def membership_records(self):
        for membrain in self.memberships():
            yield self._membership_record(membrain)

    def can_view_email(self):
        return self.get_tool('portal_membership').checkPermission('OpenPlans: View emails', self.context)

    # remove
    def membership_info_for(self, member):
        mem_id = member.getId()
        project = self.context
        project_id = project.getId()
        team = self.team
        membership = team._getOb(mem_id)

        contributions = 'XXX'
        activation = self.pretty_date(membership.made_active_date)
        modification = self.pretty_date(membership.ModificationDate())
        return dict(contributions=contributions,
                    activation=activation,
                    modification=modification,
                    )

    def is_admin(self, mem_id):
        return self.team.getHighestTeamRoleForMember(mem_id) == self.admin_role
        
# requires a reindex

