from Acquisition import aq_inner
from Products.CMFCore.permissions import DeleteObjects
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import metaconfigure, pagetemplatefile
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.PageTemplates.PageTemplate import PageTemplate
from Products.listen.browser.mail_archive_views import ArchiveForumView, ArchiveDateView, \
                                                       ArchiveNewTopicView, SubFolderDateView, \
                                                       ArchiveSearchView
from Products.listen.browser.mail_message_views import ForumMailMessageView, ThreadedMailMessageView, \
                                                       MessageReplyView, SearchDebugView
from Products.listen.browser.manage_membership import ManageMembersView
from Products.listen.browser.moderation import ModerationView as BaseModerationView
from Products.listen.config import PROJECTNAME
from Products.listen.config import MODERATION_FAILED
from Products.listen.content import ListTypeChanged
from Products.listen.interfaces.list_types import PublicListTypeDefinition, \
                                                  PostModeratedListTypeDefinition, \
                                                  MembershipModeratedListTypeDefinition
from Products.listen.interfaces import IMailingList, IMembershipModeratedList, \
                                       IPostModeratedList, IPublicList, \
                                       IWriteMembershipList, IEmailPostPolicy, \
                                       IUserEmailMembershipPolicy

from Products.listen.utilities.list_lookup import ListLookupView
from lxml.html.clean import Cleaner
from opencore.browser.formhandler import OctopoLite, action
from opencore.browser.base import BaseView, _
from opencore.listen.mailinglist import OpenMailingList
from opencore.listen.mailinglist_views import MailingListAddForm, MailingListEditForm, MailingListView
from opencore.listen.utils import isValidPrefix
from plone.app.form import _named
from plone.memoize.view import memoize as req_memoize
from zope.app.annotation.interfaces import IAnnotations
from zope.app.component.hooks import getSite
from zope.event import notify
from zope.formlib.namedtemplate import INamedTemplate
from zope.interface import implements, directlyProvides
from zExceptions import BadRequest
import cgi
import re
import new
import os.path

_ml_type_to_workflow = {
    PublicListTypeDefinition : 'policy_open',
    PostModeratedListTypeDefinition : 'policy_moderated',
    MembershipModeratedListTypeDefinition : 'policy_closed',
    }

_workflow_to_ml_type = dict((y, x) for x, y in _ml_type_to_workflow.items())

_list_error_fields = ['title', 'mailto']
def oc_json_error(v):
    return {'html': v,
            'action': 'copy',
            }
class ListenBaseView(BaseView):
    @req_memoize
    def list_url(self):
        obj = self.context
        while not IMailingList.providedBy(obj):
            try:
                obj = obj.aq_parent
            except AttributeError:
                return ''
        return obj.absolute_url()            

    @req_memoize
    def list_title(self):
        obj = self.context
        while not IMailingList.providedBy(obj):
            try:
                obj = obj.aq_parent
            except AttributeError:
                return ''
        return obj.Title()            
        
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
        req_psm2 = self.request.get("portal_status_message")
        if req_psm:
            req_psm = cgi.escape(req_psm)
            msgs.append(req_psm)
        elif req_psm2:
            req_psm2 = cgi.escape(req_psm2)
            msgs.append(req_psm2)

        return msgs

    def getSuffix(self):
        """
        Retrieves the FQDN that is the list address suffix for a site from
        the opencore_properties PropertySheet.  Requires a context object
        from inside the site so the properties tool can be retrieved.
        """
        # use threadlocal site to hook into acquisition context
        site = getSite()
        ptool = getToolByName(site, 'portal_properties')
        ocprops = ptool._getOb('opencore_properties')
        return '@' + str(ocprops.getProperty('mailing_list_fqdn').strip())

    def is_member(self, id):
        return self.get_tool('portal_memberdata').get(id) is not None



class ListenEditBaseView(ListenBaseView, OctopoLite):

    def validate_form(self, justValidate=False, creation=False):
        putils = getToolByName(self.context, 'plone_utils')
        # Create an empty dictionary to hold any eventual errors.
        self.errors = {}

        # Let's do some form validation
        # Get and clean up title from request
        title = self.request.form.get('title', '')
        title = re.compile('\s+').sub(' ', title).strip()
        # The form title variable must be unicode or listen blows up
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')

        if title:
            self.request.form['title'] = title
        else:
            self.errors['title'] = _(u'list_invalid_title', u'The mailing list must have a title.')

        # Check the list of managers
        form_managers = self.request.form.get('managers','')
        if not isinstance(form_managers, unicode):
            form_managers = unicode(form_managers, 'utf-8')
        self.request.form['managers'] = form_managers

        managers = []
        bad_managers = []
        if not form_managers:
            self.errors['managers'] = _(u'list_no_managers_error', u'The mailing list must have at least one manager.')
        else:
            for manager in form_managers.split(','):
                manager = manager.strip()
                if not self.is_member(manager):
                    bad_managers.append(manager)
                else:
                    managers.append(manager)

        if bad_managers:
            s_message_mapping = {'managers': ", ".join(bad_managers)}
            self.errors['managers'] = _(u'list_invalid_managers_error',
                                        u'The following managers are not members of this site: ${managers}',
                                        mapping=s_message_mapping)

        # Get and check the list policies
        workflow = self.request.form.get('workflow_policy')
        if workflow not in ('policy_open', 'policy_moderated', 'policy_closed'):
            self.errors['workflow_policy'] = _(u'list_invalid_workflow_error', u'The mailing list security must be set to open, moderated, or closed.')

        archive = None
        try:
            archive = int(self.request.form.get('archival_policy'))
        except TypeError:
            pass 
            
        if archive not in (0, 1, 2):
            self.errors['archive'] = _(u'list_invalid_archive_error', u'The mailing list archival method must be set to all, text-only, or none.')

        mailto = None
        if creation:
            mailto = self.request.form.get('mailto')
            if not mailto:
                self.errors['mailto'] = _(u'list_missing_prefix_error', u'The mailing list must have a list prefix.')
            elif not isValidPrefix(mailto):
                self.errors['mailto'] = _(u'list_invalid_prefix_error', u'Only the following characters are allowed in list address prefixes: alpha-numerics, underscores, hyphens, and periods (i.e. A-Z, a-z, 0-9, and _-. symbols)')
            else:
                mailto = putils.normalizeString(mailto)
                if hasattr(self.context, mailto):
                    self.errors['mailto'] = _(u'list_create_duplicate_error', u'The requested list prefix is already taken.')

        # If we don't pass sanity checks by this point, abort and let the user correct their errors.
        if self.errors and not justValidate:
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return False
        return title, workflow, archive, mailto, managers


    @action('validate')
    def validate(self, target=None, fields=None):
        putils = getToolByName(self.context, 'plone_utils')
        result = self.validate_form(justValidate=True)

        errors = dict (("oc-%s-error" % k, oc_json_error('')) for k in _list_error_fields)
        #fixme: should not be default, should be translated.        
        errors.update(dict (("oc-%s-error" % k, oc_json_error(v.default)) for k, v in self.errors.items()))
        
        mailto = self.request.form.get('mailto')
        mailto = putils.normalizeString(mailto)

        return errors


    @action('validate-members')
    def validate_members(self, target=None, fields=None):
        # Check the list of members
        form_members = self.request.form.get('members','')

        members = []
        bad_members = []
        if not form_members:
            return {
                'rejects':'',
                'valid':''
            }
        else:
            for manager in form_members.split(','):
                manager = manager.strip()
                if not self.is_member(manager):
                    bad_members.append(manager)
                else:
                    members.append(manager)
        return {
            'rejects':bad_members,
            'valid':members
        }

class ListAddView(ListenEditBaseView):

    template = ZopeTwoPageTemplateFile('create.pt')

    @action('add')
    def handle_request(self, target=None, fields=None):
        # Get the tool used to normalize strings
        putils = getToolByName(self.context, 'plone_utils')

        result = self.validate_form(creation=True)
        if not result:
            return

        title, workflow, archive, mailto, managers = result

        # Try to create a mailing list using the mailto address to see if it's going to be valid
        lists_folder = self.context
        try:
            lists_folder.invokeFactory(OpenMailingList.portal_type, mailto)
        except BadRequest:
            self.errors['mailto'] = _(u'list_create_duplicate_error', u'The requested list prefix is already taken.')
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return

        list = lists_folder._getOb(mailto)

        list.managers = tuple(managers)
        list.setDescription(unicode(self.request.form.get('description','')))

        old_workflow_type = list.list_type
        new_workflow_type = _workflow_to_ml_type[workflow]
            
        notify(ListTypeChanged(list,
                               old_workflow_type.list_marker,
                               new_workflow_type.list_marker))

        list.archived = archive

        self.template = None

        #subscribe user to list
        sub_list = IWriteMembershipList(list)
        current_user = unicode(self.loggedinmember.getId())        
        sub_list.subscribe(current_user)

        s_message_mapping = {'title': title}
        s_message = _(u'list_created',
                      u'"${title}" has been created.',
                      mapping=s_message_mapping)
        
        self.add_status_message(s_message)

        self.redirect(list.absolute_url())


class ListEditView(ListenEditBaseView):
    template = ZopeTwoPageTemplateFile('edit.pt')

    @action('edit')
    def handle_request(self, target=None, fields=None):
        result = self.validate_form()

        if not result:
            return

        title, workflow, archive, mailto, managers = result

        list = self.context

        list.setTitle(title)        
        list.setDescription(unicode(self.request.form.get('description','')))

        old_workflow_type = list.list_type
        new_workflow_type = _workflow_to_ml_type[workflow]
            
        notify(ListTypeChanged(list,
                               old_workflow_type.list_marker,
                               new_workflow_type.list_marker))

        list.archived = archive

        list.managers = tuple(managers)

        self.template = None

        s_message = _(u'list_preferences_updated',
                      u'Your changes have been saved.')
        
        self.add_status_message(s_message)

        self.redirect('%s/summary' % list.absolute_url())

    def workflow_policy(self):
        return _ml_type_to_workflow[self.context.list_type]

    def mailto(self):
        return self.context.mailto.split("@")[0]



# uh.. if you are going write meta factories you should write tests too
# isn't this what super and mixins are is suppose to solve?
def make_nui_listen_view_class(ListenClass, set_errors=False, add_update=False):
    class NuiListenView(ListenBaseView, ListenClass):
        # mask the property defined in any listen views
        context = None
        def __init__(self, context, request):
            self.context = context # MUST set context before calling the ListenClass constructor
            ListenClass.__init__(self, context, request)
            BaseView.__init__(self, context, request)

            psm = self.request.get('portal_status_message')
            
            if set_errors:
                self.errors = ()

        if add_update:
            def update(self):
                result = super(NuiListenView, self).update()
                if self.status and self.errors:
                    self.addPortalStatusMessage(self.status)
                return result

        def body(self):
            body = ListenClass.body(self)
            cleaner = Cleaner()
            body = cleaner.clean_html(body)
            if body.startswith('<p>'):
                body = body[3:-4]
            return body
    
    return NuiListenView


class ModerationView(BaseModerationView):
    """A view for moderating things """

    def __call__(self):
        #figure out request method
        method = self.request.environ['REQUEST_METHOD']
        if method == "GET":
            return self.index()

        d = self.request.form
        self.errors = ''
        post = email = None
        action = ''
        postid = None
        reject_reason = ''

        # first check if mass moderating all posts
        if d.get('discard_all_posts', False):
            action = 'discard'
            policy = getAdapter(self.context, IEmailPostPolicy)
            for post in self.get_pending_lists():
                postid = post['postid']
                email = post['user']
                req = dict(action=action, email=email, postid=postid)
                policy_result = policy.enforce(req)
                if policy_result == MODERATION_FAILED:
                    self.errors = _(u'err_could_not_moderate', u'Could not moderate!')
                    break
            return self.index()

        for name, value in d.items():
            if name.endswith('_approve') or \
               name.endswith('_discard') or \
               name.endswith('_reject'):
                action = name.split('_')[-1]
            elif name == 'postid':
                postid = int(value)
            elif name == 'email':
                email = value
            elif name == 'reject_reason':
                reject_reason = value            

        json = {}
        # having a post id specified means that we need to moderate posts
        if postid is not None:
            # using email post policy
            # may have to try enforcing the ITTWPostPolicy as well on failure
            policy = getAdapter(self.context, IEmailPostPolicy)
            req = dict(action=action, email=email, postid=postid, reject_reason=reject_reason)
            policy_result = policy.enforce(req)
            if policy_result == MODERATION_FAILED:
                self.errors = _(u'err_could_not_moderate', u'Could not moderate!')
            json = {'post_%s' % postid : {'action': 'delete'}}
        else:
            # same idea between membership policy
            # may have to try the IUserTTWMembershipPolicy if the email policy fails
            policy = getAdapter(self.context, IUserEmailMembershipPolicy)
            req = dict(action=action, email=email, reject_reason=reject_reason)
            policy_result = policy.enforce(req)
            if policy_result == MODERATION_FAILED:
                self.errors = _(u'err_could_not_moderate', u'Could not moderate!')
            json = {'member_%s' % postid : {'action': 'delete'}}
        if 'mode' in self.request.keys() and self.request.mode == 'async':
            return json
        else:
            self.redirect(self.request.ACTUAL_URL)


# prefixing everything is unnecessary
NuiMailingListView = make_nui_listen_view_class(MailingListView)


from Products.listen.interfaces import IMembershipPendingList
from zope.component import getAdapter

class SubscriptionSnippetMixin:
    def subscription_snippet(self):
        # fix #2049.
        the_list = aq_inner(self.context)
        while not IMailingList.providedBy(the_list):
            the_list = the_list.aq_parent
        return the_list.restrictedTraverse("subscription_snippet")()
    
class ArchiveForumView(SubscriptionSnippetMixin,
                       make_nui_listen_view_class(ArchiveForumView)):
    """puke a little, inherit"""

class NuiArchiveDateView(SubscriptionSnippetMixin,
                         make_nui_listen_view_class(ArchiveDateView)):
    """puke a little more"""

class NuiSubFolderDateView(SubscriptionSnippetMixin,
                           make_nui_listen_view_class(SubFolderDateView)):
    """fun fun fun"""

# XXX also, we really need flunc tests of all these views, there
# aren't any. - PW

NuiArchiveNewTopicView = make_nui_listen_view_class(ArchiveNewTopicView)
# if you don't know where you are, you don't know anything at all!
#NuiSubFolderDateView = make_nui_listen_view_class(SubFolderDateView)
NuiThreadedMailMessageView = make_nui_listen_view_class(ThreadedMailMessageView)
NuiForumMailMessageView = make_nui_listen_view_class(ForumMailMessageView)
NuiMessageReplyView = make_nui_listen_view_class(MessageReplyView)
NuiManageMembersView = make_nui_listen_view_class(ManageMembersView)
NuiModerationView = make_nui_listen_view_class(ModerationView)
NuiSearchDebugView = make_nui_listen_view_class(SearchDebugView)
NuiArchiveSearchView  = make_nui_listen_view_class(ArchiveSearchView)
NuiListLookupView = make_nui_listen_view_class(ListLookupView)


##########################################################################
# We're overriding the default NamedTemplateAdapter to work around a
# bug in plone.app.form._named.  The bug has been fixed on the Plone
# trunk.
##########################################################################

class NamedTemplateAdapter(object):
    """A named template adapter implementation that has the ability
    to lookup the template portion from regular traversal (intended for
    being able to customize the template portion of a view component
    in the traditional portal_skins style).
    """

    implements(INamedTemplate)

    def __init__(self, context):
        self.context = context

    def __call__(self, *args, **kwargs):
        """
        use aq_inner of the innermost context so we don't get a
        circular acquisition context.
        """
        view = self.context.__of__(self.context.context.aq_inner)
        cleanup = []

        # basically this means we only do customized template lookups
        # for views defined with <browser:page template='foo'> 
        if isinstance(view, metaconfigure.ViewMixinForTemplates) and \
               _named.try_portal_skins:
            index = getattr(view, 'index', None)
            if index is not None:
                name = _named.proper_name(index.filename)
                try:
                    template = view.context.portal_url.getPortalObject().restrictedTraverse(name)
                except AttributeError:
                    # ok, we couldn't find a portal_skins defined item
                    # so we fall back to the defined page template
                    template = index
                else:
                    if isinstance(getattr(template, 'aq_base', object()), PageTemplate):
                        template = _named.ViewTemplateFromPageTemplate(template,
                                                                       view.context)
                        template = template.__of__(view)
                    else:
                        template = index

            result = template(*args, **kwargs)
            return result
        else:
            return self.default_template.__of__(view)(*args, **kwargs)


def named_template_adapter(template):
    """Return a new named template adapter which defaults the to given
    template.
    """

    new_class = new.classobj('GeneratedClass', 
                             (NamedTemplateAdapter,),
                             {})
    new_class.default_template = template

    return new_class

path_prefix = os.path.split(_named.__file__)[0]
_path = os.path.join(path_prefix, 'pageform.pt')
_template = pagetemplatefile.ViewPageTemplateFile(_path)
default_named_template_adapter = named_template_adapter(_template)

_subpage_path = os.path.join(path_prefix, 'subpageform.pt')
_subpage_template = pagetemplatefile.ViewPageTemplateFile(_subpage_path)
default_subpage_template = named_template_adapter(_subpage_template)

class ListsView(BaseView):

    def can_delete_list(self):
        return self.membertool.checkPermission(DeleteObjects,
                                               self.context.aq_parent)

    def __call__(self):
        """if there is only one list and the user is not an admin,
           we automatically redirect to the mailing list"""
        list_ids = self.context.objectIds()
        if not self.can_delete_list() and len(list_ids) == 1:
            ml = getattr(self.context, list_ids[0])
            return self.redirect(ml.absolute_url())
        return self.index()
