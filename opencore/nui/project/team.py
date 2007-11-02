from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.MailHost.MailHost import MailHostError
from Products.validation.validators.BaseValidators import EMAIL_RE
from zope.event import notify
from opencore.interfaces.event import JoinedProjectEvent
from opencore.interfaces.event import LeftProjectEvent
from opencore.interfaces.event import ChangedTeamRolesEvent
from opencore.configuration import DEFAULT_ROLES
from opencore.content.membership import OpenMembership
from opencore.nui import formhandler
from opencore.nui.base import _
from opencore.nui.email_sender import EmailSender
from opencore.nui.main import SearchView
from opencore.nui.main.search import searchForPerson
from opencore.nui.member.interfaces import ITransientMessage
from opencore.nui.project import mship_messages
from opencore.nui.project.interfaces import IEmailInvites
from operator import attrgetter
from plone.memoize.instance import memoize, memoizedproperty
from plone.memoize.view import memoize as req_memoize
from plone.memoize.view import memoize_contextless
from topp.utils.detag import detag
from zope.component import getUtility
from zope.i18nmessageid import Message
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
        assert len(teams) == 1
        self.team = team = teams[0]
        self.team_path = '/'.join(team.getPhysicalPath())
        self.active_states = team.getActiveStates()
        self.sort_by = None


class RequestMembershipView(TeamRelatedView, formhandler.OctopoLite):
    """
    View class to handle join project requests.
    """
    template = ZopeTwoPageTemplateFile('request-membership.pt')

    def __call__(self):
        """ if already logged in / member of project, redirect appropriately """
        # if not logged in, redirect to the login form
        if not self.loggedin:
            self.add_status_message(_(u'team_please_sign_in', u'Please sign in to continue.'))
            self.redirect('%s/login?came_from=%s' % (self.siteURL, self.request.ACTUAL_URL))
            return
        # if already a part of the team, redirect to project home page
        if self.member_info['id'] in self.team.getActiveMemberIds():
            self.add_status_message(_(u'team_already_project_member',
                                        u'You are already a member of this project.'))
            self.redirect('%s?came_from=%s' % (self.context.absolute_url(), self.request.ACTUAL_URL))
        return super(RequestMembershipView, self).__call__()

    @formhandler.action('request-membership')
    def request_membership(self, targets=None, fields=None):
        """
        Delegates to the team object and handles destination.
        """
        if self.loggedin:
            joined = self.team.join()
        else:
            self.add_status_message(_(u'team_please_sign_in', u'Please sign in to continue.'))
            self.redirect('%s/login?came_from=%s' % (self.siteURL, self.request.ACTUAL_URL))
            return

        if joined:
            team_manage_url = "%s/manage-team" % self.context.absolute_url()
            email_vars = {'member_id': self.member_info.get('id'),
                          'project_title': self.context.title,
                          'team_manage_url': team_manage_url,
                          }
            sender = EmailSender(self, mship_messages)
            email_msg = sender.constructMailMessage('membership_requested',
                                                    **email_vars)
            request_message = self.request.form.get('request-message')
            if request_message:
                email_vars.update(member_message=detag(request_message))
                email_msg += sender.constructMailMessage('mship_request_message', **email_vars)


            mto = self.team.get_admin_ids()

            for recipient in mto:
                try:
                    sender.sendEmail(recipient, msg=email_msg, **email_vars)
                except MailHostError:
                    pass
            self.add_status_message(_(u'team_proj_join_request_sent', u'Your request to join "${project_title}" has been sent to the project administrator(s).',
                                      mapping={'project_title':self.context.Title()}))
        else:
            psmid = 'already_proj_member'
            self.add_status_message(_(u'team_already_proj_member', u'You are already a pending or active member of ${project_title}.',
                                      mapping={'project_title':self.context.Title()}))

        self.template = None # don't render the form before the redirect
        self.redirect(self.context.absolute_url())


class ProjectTeamView(TeamRelatedView):

    admin_role = DEFAULT_ROLES[-1]

   
    @formhandler.button('sort')
    def handle_request(self):
        # this is what controls which sort method gets dispatched to
        # in the memberships property
        self.sort_by = self.request.form.get('sort_by', None)

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
        member_brains = self.membranetool(**query)
        lookup_dict = dict((b.getId, b) for b in member_brains if b.getId)
        batch_dict = [lookup_dict.get(b.getId) for b in membership_brains]
        batch_dict = filter(None, batch_dict)
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

        results = sorted(results, cmp=sort_location_then_name)
        
        return self._get_batch(results, self.request.get('b_start', 0))

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
        results = self.membranetool(**query)
        return self._get_batch(results, self.request.get('b_start', 0))

    @memoizedproperty
    def memberships(self):
        try:
            sort_fn = getattr(self, 'handle_sort_%s' % self.sort_by)
            return sort_fn()
        except (TypeError, AttributeError):
            return self.handle_sort_default()
            
    def projects_for_member(self, member):
        # XXX these should be brains
        projects = self._projects_for_member(member)
        # only return max 10 results
        return projects[:10]

    def num_projects_for_member(self, member):
        projects = self._projects_for_member(member)
        return len(projects)

    @memoize_contextless
    def _projects_for_member(self, member):
        return member.getProjects()

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
        

