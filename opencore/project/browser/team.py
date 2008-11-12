from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.MailHost.MailHost import MailHostError
from Products.TeamSpace.permissions import ManageTeamMembership
from opencore.account.login import LoginView
from opencore.account.utils import email_confirmation
from opencore.browser import formhandler
from opencore.configuration import DEFAULT_ROLES
from opencore.i18n import _
from opencore.interfaces.event import JoinedProjectEvent
from opencore.interfaces.event import LeftProjectEvent
from opencore.interfaces.membership import IEmailInvites
from opencore.interfaces.message import ITransientMessage
from opencore.member.interfaces import ICreateMembers
from opencore.nui.email_sender import EmailSender
from opencore.nui.main import SearchView
from opencore.nui.main.search import searchForPerson
from opencore.project.browser import mship_messages
from opencore.utility.interfaces import IEmailSender
from operator import attrgetter
from plone.memoize.instance import memoize
from plone.memoize.instance import memoizedproperty
from plone.memoize.view import memoize as req_memoize
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.event import notify

import itertools
import operator
import re
import urllib

batch_link_re = re.compile(r'b_start:int=\d*')
end_digits_re = re.compile(r'\d*\Z')

# XXX don't need this, use key instead. -PW
## def cmp_invites(a, b):
##     return cmp(a.get('timestamp'), b.get('timestamp'))
  

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
                                      u'You are already a member of this ${project_noun}.',
                                      mapping={u'project_noun': self.project_noun}))
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
        
        sender = IEmailSender(self.portal)
        sender.sendMail(mto=email,
                        msg=message)

    # XXX get this outta here right away
    def _create(self):
        factory = ICreateMembers(self.portal)
        self.errors = factory.validate(self.request.form)
        if self.errors:
            return self.errors

        mem = factory.create(self.request.form)

        mdc = getToolByName(self.context, 'portal_memberdata')
        mem_id = mem.getId()
        code = mem.getUserConfirmationCode()
        site_url = getToolByName(self.context, 'portal_url')()
        url = "%s/confirm-account?key=%s" % (site_url, code)

        self._send_mail_to_pending_user(id=mem_id,
                                        email=self.request.get('email'),
                                        url=url)
        self.addPortalStatusMessage(_('psm_thankyou_for_joining',
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
                                  u'Your request to join "${project_title}" has been sent to the ${project_noun} administrator(s).',
                                  mapping={u'project_title':self.context.Title(),
                                           u'project_noun': self.project_noun}))
        self.template = None # don't render the form before the redirect
        self.redirect(self.context.absolute_url())


#@@ change to use utility
@req_memoize
def _email_sender(view):
    return EmailSender(view, mship_messages)

_teamview_init_defers = {}

def defer_init_action(label):
    """Decorator for formhandler actions which should cause the
    (possibly expensive) instance value initialization in the __call__
    method to be deferred.  The label argument has to be duplicated
    b/c the formhandler.action decorator uses sys._getframe(1) to get
    access to the class, so we can't call it from this decorator."""
    # XXX I don't understand how this works? -PW
    _teamview_init_defers[label] = None
    def null_decorator(fn):
        return fn
    return null_decorator


class ProjectTeamView(TeamRelatedView):
    
    admin_role = DEFAULT_ROLES[-1]

    def __init__(self, context, request):
        super(ProjectTeamView, self).__init__(context, request)
        results = None

    team_macros = ZopeTwoPageTemplateFile('team-macros.pt')

    msg_category = 'membership'

    rolemap = {'ProjectAdmin': 'Administrator',
               'ProjectMember': 'Member',
               }
    
    def __call__(self):
        try:
            action, object, fields = self.__preprocess()
        except: # XXX from octopus.py; figure out which exceptions to expect
            action, objects, fields = (None, [], [])
        if action not in _teamview_init_defers:
            self._init_values()
        self._mode = self.request.form.get('mode')
        # Purge the current user's batch_delta value if we're not an
        # AJAX request.
        if self._mode != 'async' and self.can_manage:
            # XXX maybe we don't need _batch_delta_map at all?
            # XXX See comments on _render_batch_macro. -PW
            mem_id = self._logged_in_mem_id
            batch_delta_map = getattr(self.context, '_batch_delta_map', {})
            if batch_delta_map.has_key(mem_id):
                del(batch_delta_map[mem_id])
                self.context._batch_delta_map = batch_delta_map
        return super(ProjectTeamView, self).__call__()

    # XXXX do we still need this? -PW
    @formhandler.button('sort')
    def handle_request(self):
        # this is what controls which sort method gets dispatched to
        # in the memberships property
        return 

    # XXX still used? -PW
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

        member_brains = self.results = self.membranetool(**query)
        lookup_dict = dict((b.getId, b) for b in member_brains if b.getId)
        batch_dict = [lookup_dict.get(b.getId) for b in membership_brains if lookup_dict.has_key(b.getId)]
        return self._get_batch(batch_dict, self.request.get('b_start', 0))

    @staticmethod   # still XXX used? -PW
    def sort_location_then_name(x, y):
        # XXX sort manually here, because it doesn't look like the catalog
        # has the ability to sort on multiple fields
        # @@ use advanced query???
        xloc, yloc = x.getLocation.lower(), y.getLocation.lower()
        if xloc < yloc: return -1
        if yloc < xloc: return 1
        return cmp(x.getId.lower(), y.getId.lower())

    # XXX still used? -PW
    def handle_sort_location(self):
        #mem_ids = [mem_brain.getId for mem_brain in self.membership_brains]
        query = dict(sort_on='sortableLocation',
                     #getId=mem_ids,
                     project_ids=[self.team.getId()],
                     )
        results = self.membranetool(**query)

        # @@ DRY
        self.results = sorted(results, cmp=self.sort_location_then_name)
        return self._get_batch(self.results, self.request.get('b_start', 0))

    def handle_sort_contributions(self):
        return self._get_batch([], self.request.get('b_start', 0))

    # XXX still used? -PW
    def handle_sort_default(self):
        #mem_ids = [mem_brain.getId for mem_brain in self.membership_brains]
        query = dict(portal_type='OpenMember',
                     #getId=mem_ids,
                     project_ids=[self.team.getId()],
                     sort_on='getId',
                     )
        
        # @@ DRY
        self.results = self.membranetool(**query)
        return self._get_batch(self.results, self.request.get('b_start', 0))

    @memoize #XXX where is this memoized? Is this even used anymore? -PW
    def memberships(self, sort_by=None):
        if sort_by is None:
            sort_by = self.sort_by
        sort_fn = getattr(self, 'handle_sort_%s' % sort_by,
                          self.handle_sort_default)
        return sort_fn()

    def _membership_record(self, brain):
        if type(brain) == dict:
            # it's a pending email invite, not a brain at all
            return brain

        mem_id = brain['getId']
        project = self.context
        project_id = project.getId()
        team = self.team
        membership = team._getOb(mem_id)

        contributions = 'XXX'  # Um, what's this for? -PW
        activation = self.pretty_date(membership.made_active_date)
        modification = self.pretty_date(membership.ModificationDate())

        # Filter against search returns to ensure private projects are not
        # included unless the view user is also a member.
        viewable_projects = self.all_projects_to_display

        member_projects = [viewable_projects[id_] for id_ in brain.project_ids
                           if viewable_projects.has_key(id_)]

        # sort then truncate.
        ten_projects = sorted(member_projects, key=lambda x: x.Title)[:10]

        # calculate the portrait thumbnail URL
        # XXX: default URL should come from config
        portrait_thumb_url = '++resource++img/default-portrait-thumb.gif'
        if brain.has_portrait:
            portrait_thumb_url = '%s/portrait_thumb' % brain.getURL()
        
        result = dict(activation=activation,
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

        mship_brain = self._mship_brain_map.get(brain.getId)
        if mship_brain is None and self.selector == 'pending':
            mship_brain = self._pending_mship_brain_map.get(brain.getId)
        if mship_brain is not None: # should never be None
            result['highestTeamRole'] = mship_brain.highestTeamRole
            result['lastWorkflowActor'] = mship_brain.lastWorkflowActor
            result['lastWorkflowTransitionDate'] = mship_brain.lastWorkflowTransitionDate
        return result
    

    @memoizedproperty
    def all_projects_to_display(self):
        """
        Aggregates a list of all project ids for the currently viewed
        set of members, and looks up the project brains.
        """
        proj_ids = set(itertools.chain(
            *[sorted(brain.project_ids) for brain in self.results]))

        # @@ DWM: matching on id not as good as matching on UID
        cat = self.get_tool('portal_catalog')
        pbrains = cat(getId=list(proj_ids), portal_type='OpenProject')
        return dict((b.getId, b) for b in pbrains)

    # XXX is this used? should we cache this? -PW
    def membership_records(self):
        for membrain in self.memberships():
            yield self._membership_record(membrain)

    # XXX still used? -PW
    def can_view_email(self):
        return self.get_tool('portal_membership').checkPermission('OpenPlans: View emails', self.context)

    def is_admin(self, mem_id):
        return self.team.getHighestTeamRoleForMember(mem_id) == self.admin_role
        
    # ================================================================
    # METHODS COPIED FROM SPUTNIK BELOW
    # ================================================================
    # PW notes: This adds about 800 lines of code!
    # Many handlers are 70 to 100 lines and follow the same general
    # pattern. I need to figure out a way to factor it that expresses
    # intent better and cuts down boilerplate without being overly complex.
    # Maybe handlers could be classes using a template method pattern?

    def _init_values(self):
        """initialize values that will be used by the templates"""
        # current member id.
        if self.loggedin:
            self._logged_in_mem_id = self.loggedinmember.getId()
        # active membership brains.
        query = dict(portal_type='OpenMembership',
                     path=self.team_path,
                     review_state=self.active_states,
                     )
        self._mship_brains = self.catalog(query)

        # pending membership brains.
        query = dict(portal_type='OpenMembership',
                     path=self.team_path,
                     review_state='pending',
                     )
        self.pending_mship_brains = self.catalog(query)

        # active admin and member mship brains separated, and mship
        # brain map.
        self._mship_brain_map = {}
        self.admin_mship_brains = []
        self.member_mship_brains = []
        for mship_brain in self._mship_brains:
            self._mship_brain_map[mship_brain.getId] = mship_brain
            if mship_brain.highestTeamRole == 'ProjectAdmin':
                self.admin_mship_brains.append(mship_brain)
            else:
                self.member_mship_brains.append(mship_brain)

        self._pending_mship_brain_map = {}
        for mship_brain in self.pending_mship_brains:
            self._pending_mship_brain_map[mship_brain.getId] = mship_brain

    @memoizedproperty  #XXX isn't this already cached by _init_values()? -PW
    def membership_brains(self):
        return self._mship_brains

    @property
    def selector(self):
        """Decide from the request whether we're viewing
        admins, normal members, pending members, or what.
        """
        return self.request.form.get('selector', 'member')

    # XXX write a docstring -PW
    @memoizedproperty
    def listed_mship_brains(self):
        if self.selector == 'fan':
            return []  # TODO
        return getattr(self, '%s_mship_brains' % self.selector)

##     # XXX This is unnecessary if we use key instead of cmp
##     # in self.listed_members() --PW
##     def cmp_mship_dates(self, mem1, mem2):
##         mship1 = self._pending_mship_brain_map.get(mem1.getId)
##         mship2 = self._pending_mship_brain_map.get(mem2.getId)
##         return cmp(mship1.lastWorkflowTransitionDate,
##                    mship2.lastWorkflowTransitionDate)

    @memoizedproperty
    def listed_members(self):
        mem_ids = [mem_brain.getId for mem_brain in self.listed_mship_brains]

        self.results = self.membranetool.unrestrictedSearchResults(
            portal_type='OpenMember',
            getId=mem_ids,
            sort_on='exact_getFullname', # XXX need a lowered index
            )            

        #XXX This is not used for anything? -PW
##         self._listed_member_brain_map = {}
##         for brain in self.results:
##             self._listed_member_brain_map[brain.getId] = brain
        if self.selector == 'pending':
            size = 50
            results = list(self.results)
            #results.sort(cmp=self.cmp_mship_dates, reverse=True)
            # XXX PW: use key instead, like so:
            results.sort(key=operator.attrgetter('lastWorkflowTransitionDate'),
                         reverse=True)
            self.results = self.interleave_pending(results)
        else:
            size = 25
        return self._get_batch(self.results, self.request.get('b_start', 0),
                               size=size)

    @memoizedproperty  # XXX what happens when you memoize a generator? -PW
    def listed_membership_records(self):
        for membrain in self.listed_members:
            yield self._membership_record(membrain)

    @memoizedproperty
    def pending_email_invites(self):
        invites_util = getUtility(IEmailInvites, context=self.portal)
        invites = invites_util.getInvitesByProject(self.context.getId())
        invites = [{'id': urllib.quote(address), 'address': address,
                    'timestamp': timestamp}
                   for address, timestamp in invites.items()]
        invites.sort(#cmp=cmp_invites, #XXX I'll use key instead of cmp. -PW
                     key=operator.itemgetter('timestamp'),            
                     reverse=True)
        return invites

    def interleave_pending(self, membrains):
        """List of pending mships and email invites in chronological
        order."""
        # XXX This merges pre-sorted pending_email_invites and
        # membrains, and is O(N) - but I suspect that doesn't matter
        # enough to justify the extra code as compared to a simple
        # decorate-sort-undecorate sort, which is much simpler and
        # should be O(N) + O(logN). -PW ... like so:
##         brainmap = self._pending_mship_brain_map
##         all = [(brainmap[brain.getId].lastWorkflowTransitionDate, brain)
##                for brain in membrains]
##         all.extend([(inv.get('timestamp'), inv)
##                     for inv in self.pending_email_invites]
##         all.sort(reverse=True)  # XXX not sure, is it reversed?
##         return all
        # ... And if we don't actually need the data sorted anywhere else,
        # we can remove some code elsewhere.
        # ... End of editorializing. orig code follows until it's tested.-PW
        result = []
        email_invites = self.pending_email_invites[:]
        for membrain in membrains:
            mshipbrain = self._pending_mship_brain_map.get(membrain.getId)
            for email_invite in email_invites:
                mship_timestamp = mshipbrain.lastWorkflowTransitionDate
                if email_invite.get('timestamp') >= mship_timestamp:
                    # email invite is next up
                    result.append(email_invites.pop(0))
                else:
                    # pop out of the email_invites loop
                    break
            # mship record is next up
            result.append(membrain)
        # append any remaining email invites
        result += email_invites
        return result

    @memoizedproperty
    def can_manage(self):
        mtool = getToolByName(self.context, 'portal_membership')
        return mtool.checkPermission(ManageTeamMembership, self.context)

    # XXX needed? why spelled this way? -PW
    def doMshipWFAction(self, transition, mem_ids, pred=lambda mship:True):
        """
        Fires the specified workflow transition for the memberships
        associated with the specified member ids.

        o mem_ids: list of member ids for which to fire the
        transitions.  if this isn't provided, these will be obtained
        from the request object's 'member_ids' key.
        XXX that appears to be untrue. - PW

        Returns the number of memberships for which the transition was
        successful.
        """
        team = self.team
        ids_acted_on = []
        for mem_id in mem_ids:
            mship = team._getOb(mem_id)
            if pred(mship):
                mship.do_transition(transition)
                ids_acted_on.append(mship.getId())
        return ids_acted_on

    # XXX needed? - PW
    @property
    @req_memoize
    def transient_msgs(self):
        return ITransientMessage(self.portal)

    #XXX needed? - PW
    def _add_transient_msg_for(self, mem_id, msg):
        # XXX not happy about generating the html for this here
        # but it's a one liner; can move to a macro.
        proj_url = self.context.absolute_url()
        title = self.context.Title()
        msg = '%(msg)s <a href="%(proj_url)s">%(title)s</a>' % locals()
        self.transient_msgs.store(mem_id, self.msg_category, msg)

    #XXX needed? - PW
    def mship_only_admin(self, mship):
        proj_id = self.team.getId()
        return not self._is_only_admin(proj_id, mship.getId())

    #XXX needed? document it? - PW 
    def _is_only_admin(self, proj_id, mem_id=None):
        team = self.team
        if mem_id is None:
            mem_id = self.viewed_member_info['id']

        # question is moot if member isn't active
        if mem_id not in self._mship_brain_map:
            return False

        role = team.getHighestTeamRoleForMember(mem_id)
        if role != 'ProjectAdmin':
            return False
        # looks like we mean if the member is the only admin for this proj. -PW
        return len(self.admin_mship_brains) <= 1

    # XXX needed? -PW
    def _getAccountURLForMember(self, mem_id):
        homeurl = self.membertool.getHomeUrl(mem_id)
        if homeurl is not None:
            return "%s/account" % homeurl

    # XXX needed? -PW
    def _confirmation_url(self, mem):
        # XXX is mem a member or membership? better var name. -PW
        code = mem.getUserConfirmationCode()
        root = getToolByName(self.context, 'portal_url')()
        return "%s/confirm-account?key=%s" % (root, code)

    def _render_selector(self):
        """re-render the selector snippet to update the number of
        members and admins.  Returns a dict for use as JSON."""
        html = self.render_macro(self.team_macros.macros['selector'],
                                 extra_context={'view': self})
        cmd_map = {'action': 'replace',
                   'html': html,
                   'effects': 'fadein'}
        return cmd_map

    def _render_batch_macro(self, batch_delta):
        """render the batch macro, with starting index of any higher
        batch links incremented by ``batch_delta``, taking previous
        cached values of batch_delta into consideration.
        
        Result is a snippet of HTML with links to previous and next
        batches.
        """
        # XXX RA says need to get recent oc-js for this UI to work -PW
        
        # XXX Need to better document what batch deltas are, and/or
        # come up w/ better names, or rewrite this totally..  From
        # chat w/ RA:

        # RaFromBRC: when the page is updated via ajax, it impacts the
        # batch links that are on the page. If the batch link says
        # 'next page starts at item 25', but we just removed one of
        # the first 25 entries, then the batch would actually skip
        # somebody. So, _batch_delta_map stores info so the batch
        # links can be dynamically updated so they're still correct.
        # It's cached on the project, keyed by auth user, but only for
        # async requests; the next time a user makes a non-async
        # request, the map for that user is cleared.

        # RA thinks this is "probably the place to start w/ making the
        # class smaller, pulling that stuff out so it can be used
        # elsewhere, too"
        # The caching is done because "i needed to put it somewhere
        # persistent, b/c it has to span multiple requests".
        # "... if i remove 3 people from a project, for instance,
        # that's 3 successive ajax requests... i need to decrement the
        # batch links by 3 ...  or, by one each time, to be more
        # precise."

        # XXX _batch_delta_map should be a PersistentDict to reduce
        # project writes. RA concurs. -PW

        # XXX OR... maybe this is totally the wrong approach.  We
        # already have the rendered HTML on the page.  Why don't we
        # just decrement the numbers totally client-side and skip this
        # call completely?  We'd also have to update everything that
        # uses these numbers: search-results-summary, which is used to
        # say eg. "Members 1 through 24 of 43" at bottom of page.  The
        # markup of that should be changed to make it easier. And
        # _render_search_summary() could then go away too.  I think
        # that's all.  I think I wanna try that and get code working
        # before I even talk to RA about it. -PW
        
        # first decrement existing batch delta
        batch_delta_map = getattr(self.context, '_batch_delta_map', {})
        batch_delta = batch_delta_map.get(self._logged_in_mem_id,
                                          0) + batch_delta
        batch_delta_map[self._logged_in_mem_id] = batch_delta
        self.context._batch_delta_map = batch_delta_map

        # instantiate the batch_view and set up extra_context
        batch_view = getMultiAdapter((self.context, self.request),
                                     name=u'nui_batch_macros')
        extra_context = {'batch': self.listed_members,
                         'template_id': self.__name__,
                         'batch_base_url': '/'.join((self.context.absolute_url(),
                                                     self.__name__))
                         }
        # clear out the form so we don't get query string cruft in
        # our batch URLs
        req_form = self.request.form
        self.request.form = {}
        html = self.render_macro(batch_view.index.macros['pagination'],
                                 extra_context=extra_context)
        # put the request form back
        self.request.form = req_form
        b_start = self.request.get('b_start', 0)
        # iterate through the links and decrement the higher ones

        # XXX Munging the generated html with regexes. Could we just
        # generate the correct html in the first place?  -PW
        for batch_link in batch_link_re.findall(html):
            link_start = int(end_digits_re.search(batch_link).group())
            # only edit the one past our current position
            if link_start > b_start:
                new_batch_link = batch_link.replace(str(link_start),
                                                    str(link_start +
                                                        batch_delta))
                html = html.replace(batch_link, new_batch_link)
        cmd_map = {'action': 'replace-by-query',
                   'html': html,
                   'effects': 'fadein'}
        return cmd_map

    # XXX Kill this? See comments on _batch_delta_map. -PW
    def _render_search_summary(self):
        """re-render the search results summary macro for an AJAX
        operation; must be called AFTER _render_batch_macro b/c that
        adjusts the _batch_delta_map that this depends on.
        Returns a dict for use as JSON."""
        batch = self.listed_members
        batch_delta_map = self.context._batch_delta_map
        batch_delta = batch_delta_map[self._logged_in_mem_id]
        start = batch.start
        seq_length = batch.sequence_length
        if batch.end == seq_length:
            end = seq_length
        else:
            end = batch.end + batch_delta
        extra_context = {'start': start,
                         'end': end,
                         'many': start != end,
                         'sequence_length': seq_length}
        macro = self.team_macros.macros['search-results-summary']
        html = self.render_macro(macro, extra_context=extra_context)
        cmd_map = {'action': 'replace',
                   'html': html,
                   'effects': 'fadein'}
        return cmd_map

    # XXX why is this done in code and not template? -PW
    def _render_num_members(self):
        """render the '# members.' piece at the top of the page.
        Returns a snippet of HTML.
        """
        n = len(self._mship_brains)
        plural = n == 1 and '' or 's'
        html = '<span id="num-members">%d member%s.</span>' % (n, plural)
        return html

    # REMOVE MEMBER BUTTON HANDLER
    @formhandler.action('remove-members')
    @defer_init_action('remove-members')
    def remove_members(self, targets, fields=None):
        """
        Doesn't actually remove the membership objects, just
        puts them into an inactive workflow state.
        """
        mem_ids = targets
        mems_removed = self.doMshipWFAction('deactivate', mem_ids,
                                            self.mship_only_admin)
        sender = _email_sender(self)
        result = {}
        mdtool = getToolByName(self.context, 'portal_memberdata')
        mdtoolpath = '/'.join(mdtool.getPhysicalPath())
        
        for mem_id in mems_removed:
            mship = self.team._getOb(mem_id)
            notify(LeftProjectEvent(mship))

            mem_path = '%s/%s' % (mdtoolpath, mem_id) 
            try:
                mem_metadata = self.catalog.getMetadataForUID(mem_path) 
                mem_user_name = mem_metadata['getFullname'] or mem_metadata['id']
            except KeyError:
                mem_user_name = mem_id

            msg_subs = {
                'project_title': self.context.title,
                'user_name': mem_user_name,
                'project_noun':self.project_noun,
                }
            try:
                # XXX sending an email should be in an event handler.
                sender.sendEmail(mem_id, msg_id='membership_deactivated',
                                 **msg_subs)
            except MailHostError:
                self.add_status_message(_(u'psm_error_sending_mail_to_member',
                                          'Error sending mail to: ${mem_id}',
                                          mapping={u'mem_id': mem_id}))
            # XXX should this PSM be in an event handler too? -PW
            self._add_transient_msg_for(mem_id, 'You have been deactivated from')
            # delete the member row from the AJAX UI.
            result[mem_id] = {'action': 'delete'}

        self._init_values()
        if mems_removed:
            plural = len(mems_removed) != 1
            msg = "Member%s deactivated: %s" % (plural and 's' or '',
                                                ', '.join(mems_removed))

            if self._mode == 'async':
                # instantiate a new view to recalculate member lists, etc.
                # replace the selector snippet
                result['selector-snippet'] = self._render_selector()
                # replace batch snippets
                result['.oc-paginator'] = self._render_batch_macro(-len(mems_removed))
                # replace search results summary
                result['search-resuls-summary'] = self._render_search_summary()
                # replace the num-members snippet at top of page
                result['num-members'] = {'action': 'replace',
                                         'html': self._render_num_members(),
                                         'effects': 'fadein'}
            self.team.reindexTeamSpaceSecurity()

        elif mem_ids:
            msg = 'Cannot remove last admin: %s' % mem_ids[0]
        else:
            msg = 'Please select members to remove.'
        self.add_status_message(msg)

        return result


    # XXX 100 lines is just too much for one method. -PW
    # MEMBER SET ROLE BUTTON HANDLER
    @formhandler.action('set-roles')
    @defer_init_action('set-roles')
    def set_roles(self, targets, fields):
        """
        Brings the stored team roles into sync with the values stored
        in the request form.
        """
        # XXX what are these fields? -PW
        roles = [f.get('role') for f in fields]
        roles_from_form = dict(zip(targets, roles))

        team = self.team
        changes = []
        for mem_id in roles_from_form:
            from_form = roles_from_form[mem_id]
            if team.getHighestTeamRoleForMember(mem_id) != from_form:
                index = DEFAULT_ROLES.index(from_form)
                mem_roles = DEFAULT_ROLES[:index + 1]
                team.setTeamRolesForMember(mem_id, mem_roles)
                changes.append(mem_id)

        if not changes:
            msg = u"No roles changed"
            self.add_status_message(msg)
            return

        self._init_values()
        # make sure self.results is set so base class is happy
        # XXX this is now in the base class! :) -PW
        if getattr(aq_base(self), 'results', None) is None:
            unused = self.listed_members
        result = {}
        batch_delta = 0
        for mem_id in changes:
            brain = self.membranetool(portal_type='OpenMember',
                                      exact_getUserName=mem_id)
            if not brain:
                # XXX this should not happen. -PW
                continue
            brain = brain[0]
            team_role = team.getHighestTeamRoleForMember(mem_id)
            role_selector_value = self.rolemap[team_role].lower()
            selector = self.request.get('selector', 'member')
            if self._mode == 'async':
                undo = role_selector_value.startswith(selector)
                member_record = self._membership_record(brain)
                if undo:
                    batch_delta += 1
                    # update the member row
                    extra_context={'member_record': member_record,
                                   'team_macros': self.team_macros,
                                   'changeable': True,
                                   'can_manage': self.can_manage,
                                   'member_role': team_role,}
                    html = self.render_macro(self.team_macros.macros['member-row'],
                                             extra_context=extra_context)
                else:
                    # we've changed to not match the others on the screen
                    batch_delta -= 1
                    # jump through a hoop to figure out the right team role
                    # for the current page (reverse lookup by selector)
                    rolemap = self.rolemap
                    undo_role = [r for r in rolemap if
                                 rolemap[r].lower().startswith(selector)][0]
                    mtool = getToolByName(self.context, 'portal_membership')
                    home_url = mtool.getHomeUrl(member_record['id'])
                    extra_context={'member_record': member_record,
                                   'member_role': rolemap[team_role],
                                   'selector': selector,
                                   'b_start': self.request.get('b_start', 0),
                                   'undo_role': undo_role,
                                   'home_url': home_url}
                    html = self.render_macro(self.team_macros.macros['member-role-changed'],
                                             extra_context=extra_context)
                result[mem_id] = {'action': 'replace',
                                  'html': html,
                                  'effects': 'highlight'}

            promoted = team_role == 'ProjectAdmin' #XXX use DEFAULT_ROLES[-1]? -PW
            if promoted:
                transient_msg = 'You are now an admin of'
                status_msg = _(u'promote_to_admin',
                               mapping={'name': mem_id})
            else:
                transient_msg = 'You are no longer an admin of'
                status_msg = _(u'demote_to_member',
                               mapping={'name': mem_id})
            self._add_transient_msg_for(mem_id, transient_msg)
            self.add_status_message(status_msg)

        if self._mode == 'async':
            # replace various snippets in the AJAX UI.
            result['selector-snippet'] = self._render_selector()
            result['.oc-paginator'] = self._render_batch_macro(batch_delta)
            result['search-results-summary'] = self._render_search_summary()
        return result

    # MEMBER SEARCH BUTTON HANDLER
    @formhandler.action('search-members')
    def search_members(self, targets=None, fields=None):
        """
        Performs the catalog query and then puts the results in an
        attribute on the view object for use by the template.  Filters
        out any members for which a team membership already exists,
        since this is used to add new members to the team.
        """
        filtered_states = ('pending', 'private', 'public')
        existing_ids = self.team.getMemberIdsByStates(filtered_states)
        existing_ids = dict.fromkeys(existing_ids)

        search_for = self.request.form.get('search_for')
        if not search_for:
            self.add_status_message(u'Please enter search text.')
            return
        results = searchForPerson(self.membranetool, search_for)
        results = [r for r in results if r.getId not in existing_ids]
        self.search_results = results
        if not len(results):
            self.add_status_message(u'No members were found.')

    def _doInviteMember(self, mem_id):
        """
        Perform the actual membership invitation, either by creating a
        membership object or firing the reinvite transition.
        """
        if not mem_id in self.team.getMemberIds():
            # XXX hmm, how is this an invite? we give the member no choice! -PW
            # create the membership
            self.team.addMember(mem_id, reindex=False)
        else:
            # reinvite existing membership
            wftool = self.get_tool('portal_workflow')
            mship = self.team.getMembershipByMemberId(mem_id)
            transitions = wftool.getTransitionsFor(mship)
            if 'reinvite' not in [t['id'] for t in transitions]:
                return False
            wftool.doActionFor(mship, 'reinvite')
        return True

    # MEMBER INVITE BUTTON HANDLER
    @formhandler.action('invite-member')
    @defer_init_action('invite-member')
    def invite_member(self, targets, fields=None):
        """
        Sends an invitation notice, and creates a pending membership
        object (or puts the existing member object into the pending
        state).  The member id is specified in the request form, as
        the value for the 'invite-member' button.
        """
        mem_id = targets[0] # should only be one
        if not self._doInviteMember(mem_id):
            # XXX when does this happen?
            self.add_status_message(u'You cannot reinvite %s to join this %s yet.' % (mem_id, self.project_noun))
            self.redirect('%s/manage-team' % self.context.absolute_url())
            # XXX isn't that URL a redirect now? -PW

        # XXX if member hasn't logged in yet, acct_url will be whack
        acct_url = self._getAccountURLForMember(mem_id)
        logged_in_mem = self.loggedinmember #XXX useless temp var. -PW
        logged_in_mem_name = logged_in_mem.getFullname() or logged_in_mem.id

        mdtool = getToolByName(self.context, 'portal_memberdata')
        mdtoolpath = '/'.join(mdtool.getPhysicalPath())
        mem_path = '%s/%s' % (mdtoolpath, mem_id) 
        mem_metadata = self.catalog.getMetadataForUID(mem_path) 
        mem_user_name = mem_metadata['getFullname'] or mem_metadata['id']

        msg_subs = {
                'project_title': self.context.title,
                'account_url': acct_url,
                'user_name': mem_user_name,
                'inviter_name': logged_in_mem_name,
                'portal_name': self.portal.title,
                'portal_url': self.portal.absolute_url(),
                }
        _email_sender(self).sendEmail(mem_id, msg_id='invite_member',
                                      **msg_subs)
        self._clear_instance_memos()
        self._init_values()
        self.add_status_message(u'You invited %s to join this %s' % (mem_id, self.project_noun))

    # APPROVE MEMBERSHIP REQUEST BUTTON HANDLER
    @formhandler.action('approve-request')
    @defer_init_action('approve-request')
    def approve_request(self, targets, fields=None):
        if not targets:
            self.add_status_message(_(u'psm_please_select_members',
                                      u'Please select members to approve.'))
            return {}
        mem_ids = targets
        wftool = self.get_tool('portal_workflow')

        napproved = 0
        res = {}
        for mem_id in mem_ids:
            mship = self.team._getOb(mem_id)
            # approval transition has a different id for public and
            # private, have to look up by name
            transition = [t for t in wftool.getTransitionsFor(mship)
                          if t.get('name') == 'Approve']
            if not transition:
                continue
            transition_id = transition[0]['id']
            wftool.doActionFor(mship, transition_id)
            napproved += 1

            notify(JoinedProjectEvent(mship))

            mdtool = getToolByName(self.context, 'portal_memberdata')
            mdtoolpath = '/'.join(mdtool.getPhysicalPath())
            mem_path = '%s/%s' % (mdtoolpath, mem_id) 
            mem_metadata = self.catalog.getMetadataForUID(mem_path) 
            mem_user_name = mem_metadata['getFullname'] or mem_metadata['id']

            msg_subs = {
                'project_title': self.context.title,
                'user_name': mem_user_name,
                'project_noun': self.project_noun,
                'portal_url': self.portal.absolute_url(),
                'project_url': self.project_url(self.context.getId()),
                }
            #XXX sending the email should go in an event subscriber
            try:
                _email_sender(self).sendEmail(mem_id, msg_id='request_approved',
                                              **msg_subs)
            except MailHostError: 
                pass
            self._add_transient_msg_for(mem_id, 'You have been accepted to')

            # delete member row
            res[mem_id] = {'action': 'delete'}

        if napproved == 1:
            self.add_status_message(_(u'psm_one_request_approved', u'You have added ${mem_id}.',
                                      mapping={u'mem_id':mem_id}))
        else:
            self.add_status_message(_(u'psm_many_requests_approved', u'You have added ${num_approved} members.'
                                      , mapping={u'num_approved':napproved}))
        if napproved:
            self.team.reindexTeamSpaceSecurity()

        self._init_values()
        if self._mode == 'async':
            # replace various snippets in ajax UI.
            res['selector-snippet'] = self._render_selector()
            res['.oc-paginator'] = self._render_batch_macro(-len(mem_ids))
            res['search-results-summary'] = self._render_search_summary()
            res['num-members'] = {'action': 'replace',
                                  'html': self._render_num_members(),
                                  'effects': 'fadein'}
        return res


    # DENY MEMBERSHIP REQUEST BUTTON HANDLER
    @formhandler.action('deny-request')
    @defer_init_action('deny-request')
    def deny_request(self, targets, fields=None):
        if not targets:
            self.add_status_message(u'Please select members to deny.')
            return {}

        # copy targets list b/c manage_delObjects empties the list
        mem_ids = targets[:]
        self.doMshipWFAction('reject_by_admin', mem_ids)
        sender = _email_sender(self)

        mdtool = getToolByName(self.context, 'portal_memberdata')
        mdtoolpath = '/'.join(mdtool.getPhysicalPath())
        res = {}
        for mem_id in mem_ids:
            mem_path = '%s/%s' % (mdtoolpath, mem_id) 
            mem_metadata = self.catalog.getMetadataForUID(mem_path) 
            mem_user_name = mem_metadata['getFullname'] or mem_metadata['id']

            msg_subs = {
                'project_title': self.context.title,
                'user_name': mem_user_name,
                'project_noun': self.project_noun,                
                }
        
            msg = sender.constructMailMessage('request_denied', **msg_subs)
            sender.sendEmail(mem_id, msg=msg)
            self._add_transient_msg_for(mem_id, 'You have been denied membership to')

            # delete the member row
            res[mem_id] = {'action': 'delete'}

        plural = len(mem_ids) != 1
        msg = u"Request%s denied: %s" % (plural and 's' or '', ', '.join(mem_ids))
        self.add_status_message(msg)

        self._init_values()
        if self._mode == 'async':
            # replace various snippets via ajax.
            res['selector-snippet'] = self._render_selector()
            res['.oc-paginator'] = self._render_batch_macro(-len(mem_ids))
            res['search-results-summary'] = self._render_search_summary()
        return res


    # REMIND INVITE BUTTON HANDER
    @formhandler.action('remind-invite')
    def remind_invite(self, targets, fields=None):
        mem_ids = targets
        project_title = self.context.Title()
        sender = _email_sender(self)
        mdtool = getToolByName(self.context, 'portal_memberdata')
        mdtoolpath = '/'.join(mdtool.getPhysicalPath())
        logged_in_mem = self.loggedinmember
        logged_in_mem_name = logged_in_mem.getFullname() or logged_in_mem.id
        
        for mem_id in mem_ids:
            acct_url = self._getAccountURLForMember(mem_id)
            mem_path = '%s/%s' % (mdtoolpath, mem_id) 
            mem_metadata = self.catalog.getMetadataForUID(mem_path) 
            mem_user_name = mem_metadata['getFullname'] or mem_metadata['id']

            msg_vars = {'project_title': project_title,
                        'user_name': mem_user_name,
                        'account_url': acct_url,
                        'inviter_name': logged_in_mem_name,
                        }

            if mem_metadata['review_state'] == 'pending':
                mem = mdtool.get(mem_id)
                msg_vars['conf_url'] = self._confirmation_url(mem)
                sender.sendEmail(mem_id, msg_id='remind_pending_invitee', **msg_vars)
            else:
                sender.sendEmail(mem_id, msg_id='remind_invitee', **msg_vars)

        if not mem_ids:
            self.add_status_message(_(u"remind_invite_none_selected"))
        else:
            plural = len(mem_ids) != 1
            msg = "Reminder%s sent: %s" % (plural and 's' or '', ", ".join(mem_ids))
            self.add_status_message(msg)
        return

    # RETRACT INVITE BUTTON HANDER
    @formhandler.action('retract-invite')
    @defer_init_action('retract-invite')
    def retract_invitations(self, targets, fields=None):
        """
        Deletes (or deactivates, if there's history to preserve) the
        membership objects.  Should send notifiers.
        """
        mem_ids = targets
        wftool = self.get_tool('portal_workflow')
        wf_tool = getToolByName(self, 'portal_placeful_workflow')
        deletes = []
        sender = _email_sender(self)
        
        msg_subs = {
                'project_title': self.context.title,
                'project_noun': self.project_noun,
                }
        msg = sender.constructMailMessage('invitation_retracted',
                                          **msg_subs)
        config = wf_tool.getWorkflowPolicyConfig(self.team)
        if config is not None:
            wf_ids = config.getPlacefulChainFor('OpenMembership')
            wf_id = wf_ids[0]
        else:
            wf_id = 'openplans_team_membership_workflow'
        res = {}
        for mem_id in mem_ids:
            mship = self.team.getMembershipByMemberId(mem_id)
            status = wftool.getStatusOf(wf_id, mship)
            if status.get('action') == 'reinvite':
                # deactivate
                wftool.doActionFor(mship, 'deactivate')
            else:
                # delete
                deletes.append(mem_id)
            res[mem_id] = {'action': 'delete'}
            if email_confirmation():
                sender.sendEmail(mem_id, msg=msg)

        if deletes:
            self.team.manage_delObjects(ids=deletes)

        plural = len(mem_ids) != 1
        msg = u'Invitation%s removed: %s' % (plural and 's' or '', ', '.join(mem_ids))
        self.add_status_message(msg)

        self._init_values()
        # replace various snippets in ajax UI
        res['selector-snippet'] = self._render_selector()
        res['.oc-paginator'] = self._render_batch_macro(-len(mem_ids))
        res['search-results-summary'] = self._render_search_summary()
        return res

    @formhandler.action('retract-email-invite')
    def remove_email_invites(self, targets, fields=None):
        """
        Retracts invitations sent to email addresses.  Should send
        notifiers.
        """
        addresses = [urllib.unquote(t).strip() for t in targets]

        sender = _email_sender(self)
        msg_subs = {
                'project_title': self.context.Title(),
                'project_noun': self.project_noun,
                }
        msg = sender.constructMailMessage('invitation_retracted',
                                          **msg_subs)

        invite_util = getUtility(IEmailInvites, context=self.portal)
        proj_id = self.context.getId()
        for address in addresses:
            invite_util.removeInvitation(address, proj_id)
            if email_confirmation():
                sender.sendEmail(address, msg=msg)

        plural = len(addresses) != 1
        msg = u'Email invitation%s removed: %s' % (plural and 's' or '',', '.join(addresses))
        self.add_status_message(msg)

        res = dict([(urllib.quote(target), {'action': 'delete'})
                    for target in targets])
        return res
