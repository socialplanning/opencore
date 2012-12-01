from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.account.login import LoginView
from opencore.browser import formhandler
from opencore.configuration import DEFAULT_ROLES
from opencore.i18n import _
from opencore.member.interfaces import ICreateMembers
from opencore.nui.main import SearchView
from opencore.utility.interfaces import IEmailSender
from operator import attrgetter
from plone.memoize.instance import memoizedproperty
from plone.memoize.instance import memoize
from zope.component import getMultiAdapter

class TeamRelatedView(SearchView):
    """
    Base class for views on the project that are actually related to
    the team and team memberships.
    """

    @property
    def team_path(self):
        return '/'.join(self.team.getPhysicalPath())

    @memoizedproperty
    def active_states(self):
        return self.team.getActiveStates()
    
    @memoizedproperty
    def team(self):
        teams = self.context.getTeams()
        assert len(teams) == 1, "%d teams. 1 expected" %len(teams)
        return teams[0]
        

from opencore.account.join import BaseJoinView

class RequestMembershipView(TeamRelatedView, formhandler.OctopoLite, LoginView, BaseJoinView):
    """
    View class to handle join project requests.
    """
    template = ZopeTwoPageTemplateFile('request-membership.pt')

    def __call__(self):
        """ if already member of project, redirect appropriately """
        # if already a part of the team, redirect to project home page
        if self.member_info.get('id') in self.team.getActiveMemberIds():
            self.add_status_message(_(u'team_already_project_member',
                                      u'You are already a member of this ${project_noun}.',
                                      mapping={u'project_noun': self.project_noun}))
            self.redirect('%s?came_from=%s' % (self.context.absolute_url(), 
                                               self.request.getURL()))
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
    def _send_mail_to_pending_user(self, id, email, url):
        """ send a mail to a pending user """
        # TODO only send mail if in the pending workflow state
        mailhost_tool = self.get_tool("MailHost")
        site_url = getToolByName(self.context, 'portal_url')()
        message = _(u'email_to_pending_user',
                    mapping={u'user_name':id,
                             u'url':url,
                             u'portal_url': site_url,
                             u'portal_title':self.portal_title()})
        
        subject = _(u'email_to_pending_user_subject',
                    mapping={u'user_name':id,
                             u'url':url,
                             u'portal_url': site_url,
                             u'portal_title':self.portal_title()})
        
        sender = IEmailSender(self.portal)
        sender.sendMail(mto=email,
                        msg=message,
                        subject=subject)

    # XXX get this outta here right away
    def _create(self):
        factory = ICreateMembers(self.portal)
        self.errors = factory.validate(self.request)

        viewlet_mgr = getMultiAdapter((self.context, self.request, self),
                                      name='opencore.create_account')
        if not hasattr(viewlet_mgr, 'viewlets'):
            # This means it hasn't had update() called yet. only do that once.
            viewlet_mgr.update()
        for viewlet in viewlet_mgr.viewlets:
            if hasattr(viewlet, 'validate'):
                self.errors.update(viewlet.validate())

        if self.errors:
            return self.errors

        for viewlet in viewlet_mgr.viewlets:
            if hasattr(viewlet, 'save'):
                viewlet.save()

        mem = factory.create(self.request.form)

        mdc = getToolByName(self.context, 'portal_memberdata')
        mem_id = mem.getId()
        code = mem.getUserConfirmationCode()
        site_url = getToolByName(self.context, 'portal_url')()
        url = "%s/confirm-account?key=%s" % (site_url, code)

        self._send_mail_to_pending_user(id=mem_id,
                                        email=self.request.get('email'),
                                        url=url)
        self.addPortalStatusMessage(_('psm_thankyou_for_joining_to_team',
                                      u'Thanks for joining ${portal_title}, ${mem_id}!\nA confirmation email has been sent to you with instructions on activating your account. After you have activated your account, your request to join the ${project_noun} will be sent to the ${project_noun} administrators.',
                                      mapping={u'mem_id':mem_id,
                                               u'portal_title':self.portal_title(),
                                               u'project_noun': self.project_noun,
                                               }))
        return mdc._getOb(mem_id)

    @formhandler.action('request-membership')
    def request_membership(self, targets=None, fields=None):
        """
        Delegates to the team object and handles destination.
        """

        from opencore import recaptcha
        if not recaptcha.confirm(self.request['REMOTE_ADDR'], 
                                 self.request.form.get("recaptcha_challenge_field"),
                                 self.request.form.get("recaptcha_response_field")):
            self.addPortalStatusMessage("Invalid CAPTCHA, please try again.")
            self.redirect(self.context.absolute_url())
            return 

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
                                      mapping={'project_title':self.context.Title().decode('utf-8')}))
            self.template = None # don't render the form before the redirect
            self.redirect(self.context.absolute_url())
            return

        self.add_status_message(_(u'team_proj_join_request_sent',
                                  u'Your request to join "${project_title}" has been sent to the ${project_noun} administrator(s).',
                                  mapping={u'project_title':self.context.Title().decode('utf-8'),
                                           u'project_noun': self.project_noun}))
        self.template = None # don't render the form before the redirect
        self.redirect(self.context.absolute_url())


from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
class ProjectTeamView(TeamRelatedView):

    admin_role = DEFAULT_ROLES[-1]

    def lineup_class(self):
        return "oc-roster"

    def __call__(self):
        # @@ why is this redirect here? DWM
        # these view represent different functions
        if self.get_tool('portal_membership').checkPermission('TeamSpace: Manage team memberships', self.context):
            self.redirect(self.context.absolute_url() + '/manage-team')
        else:
            return super(ProjectTeamView, self).__call__()

    _heading_block  = ZopeTwoPageTemplateFile('team-heading.pt')
    def heading_block(self, batch):
        return self._heading_block(batch=batch)

    def handle_request(self):
        # this is what controls which sort method gets dispatched to
        # in the memberships property
        sort_by = self.request.form.get('sort_by')
        if sort_by is None:
            search_results = self.handle_sort_default()

        if sort_by == 'location':
            search_results = self.handle_sort_location()
        elif sort_by == 'membership_date':
            search_results = self.handle_sort_membership_date()
        elif sort_by == 'username':
            search_results = self.handle_sort_default()

        return search_results

    def handle_sort_membership_date(self):
        # XXX for some reason, the descending sort is not working properly
        # seems to only want to be ascending
        # so let's just use python sort to sort the results ourselves
        membership_brains = sorted(
            self.membership_brains,
            key=attrgetter('made_active_date'),
            reverse=True)

        mem_ids = [b.getId for b in membership_brains]
        
        query = dict(portal_type='OpenMember',
                     getId=mem_ids,
                     )

        member_brains = self.membranetool(**query)

        # @@ what do these two lines do?
        lookup_dict = dict((b.getId, b) for b in member_brains if b.getId)
        batch_dict = [lookup_dict.get(b.getId) for b in membership_brains if lookup_dict.has_key(b.getId)]
        
        return batch_dict

    @staticmethod
    def sort_location_then_name(x, y):
        # XXX sort manually here, because it doesn't look like the catalog
        # has the ability to sort on multiple fields
        # @@ use advanced query???
        xloc, yloc = x.getLocation.lower(), y.getLocation.lower()
        if xloc < yloc: return -1
        if yloc < xloc: return 1
        return cmp(x.getId.lower(), y.getId.lower())

    @memoizedproperty
    def membership_brains(self):
        query = dict(portal_type='OpenMembership',
                 path=self.team_path,
                 review_state=self.active_states,
                 )
        return self.catalog(**query)

    
    def handle_sort_location(self):
        #mem_ids = [mem_brain.getId for mem_brain in self.membership_brains]
        query = dict(sort_on='sortableLocation',
                     #getId=mem_ids,
                     project_ids=[self.team.getId()],
                     )
        results = self.membranetool(**query)

        # @@ DRY
        results = sorted(results, cmp=self.sort_location_then_name)

        return results

    def handle_sort_contributions(self):

        return []

    def handle_sort_default(self):
        query = dict(portal_type='OpenMember',
                     project_ids=[self.team.getId()],
                     sort_on='sortable_title',
                     )
        # @@ DRY
        results = self.membranetool(**query)

        return results

    @memoize
    def memberships(self, sort_by=None):
        if sort_by is None:
            sort_by = self.sort_by
        sort_fn = getattr(self, 'handle_sort_%s' % sort_by,
                          self.handle_sort_default)
        return sort_fn()

    def _membership_record(self, brain):
        mem_id = brain['getId']
        project = self.context
        project_id = project.getId()
        team = self.team
        membership = team._getOb(mem_id)

        contributions = 'XXX'
        made_active_date = getattr(aq_base(membership), 'made_active_date',
                                           None)
        if made_active_date is not None:
            activation = self.pretty_date(made_active_date)
        else:
            activation = 'never'
        modification = self.pretty_date(membership.ModificationDate())

        # Filter against search returns to ensure private projects are not
        # included unless the view user is also a member.

        # We can quickly filter by passing the unrestricted list of project ids
        # into the catalog tool's restricted search for projects
        # XXX TODO: this might be nice to provide as a function in opencore.project?
        cat = self.get_tool('portal_catalog')
        member_projects = cat(getId=list(brain.project_ids),
                              portal_type='OpenProject')

        # sort then truncate
        ten_projects = sorted(member_projects, key=lambda x: x.Title)[:10]

        # calculate the portrait thumbnail URL
        # XXX: default URL should come from config
        portrait_thumb_url = '++resource++img/default-portrait-thumb.gif'
        if brain.has_portrait:
            portrait_thumb_url = '%s/portrait_thumb' % brain.getURL()
        
        return dict(activation=activation,
                    contributions=contributions,
                    email=brain.getEmail,
                    fullname=brain.getFullname,
                    id=mem_id,
                    location=brain.getLocation,
                    modification=modification,
                    portrait_thumb_url=portrait_thumb_url,
                    project_brains=ten_projects,
                    num_projects=len(member_projects)
                    )

    def can_view_email(self):
        return self.get_tool('portal_membership').checkPermission('OpenPlans: View emails', self.context)

    def is_admin(self, mem_id):
        return self.team.getHighestTeamRoleForMember(mem_id) == self.admin_role
        

