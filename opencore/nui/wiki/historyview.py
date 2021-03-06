from BTrees.IOBTree import IOBTree
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.interfaces.IArchivist import ArchivistRetrieveError
from Products.Five import BrowserView
from opencore.browser.base import BaseView
from opencore.browser.formhandler import post_only
from opencore.i18n import _
from opencore.i18n import translate
from opencore.interfaces.catalog import ILastModifiedAuthorId, ILastModifiedComment
from opencore.nui.wiki import htmldiff2
from opencore.nui.wiki import utils
from opencore.nui.wiki.interfaces import IWikiHistory, IReversionEvent
from opencore.project.browser.metadata import get_member
from plone.memoize import instance
from topp.utils.pretty_date import prettyDate
from view import WikiBase
from zExceptions import Redirect
from zope.app.annotation.interfaces import IAnnotations
from zope.app.event.objectevent import ObjectModifiedEvent
from zope.event import notify
from zope.interface import alsoProvides, implements


class WikiVersionView(WikiBase): 

    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        self.pr = self.get_tool('portal_repository')

    def get_page(self, version_id):
        doc = self.pr.retrieve(self.context, version_id)
        return doc.object
        
    def get_versions(self):
        """
        Returns a list of versions on the object.
        """
        return IWikiHistory(self.context)
        #return self.pr.getHistory(self.context, countPurged=False)

    def get_version(self, version_id):
        version_id = int(version_id)
        return self.pr.retrieve(self.context, version_id)

    def version_title(self, version_id, rollback=False):
        if version_id == 0:
            return _(u'version_initial_title', u"Initial Version")
        elif version_id == self.current_id() and not rollback:
            return _(u'version_current_title', u"Current Version")
        else: 
            return _(u'version_requested_title', "Version ${version_num}",
                     mapping={'version_num': version_id + 1})

    def current_id(self): 
        return len(self.get_versions()) - 1

    def previous_id(self, version_id): 
        if version_id == 0:
            return None
        else:
            return version_id - 1
    
    def next_id(self, version_id): 
        if version_id == self.current_id():
            return None
        else:
            return version_id + 1
            
    def pretty_mod_date(self, version):
        if isinstance(version, dict):
            value = version['modification_date']
        else:
            try:
                value = DateTime(version.sys_metadata['timestamp'])
            except AttributeError:
                value = version
        return prettyDate(value)

    def can_revert(self):
        return self.get_tool('portal_membership').checkPermission('CMFEditions: Revert to previous versions', self)

    @post_only(raise_=True)
    def rollback_version(self, version_id=None):
        if version_id is None:
            version_id=self.request.get('version_id')
        
        # error check parameters
        req_error = None
        view_url = self.context.absolute_url()
        
        try:
            curr_id = self.current_id()
            version_id = int(version_id)
            if version_id < 0 or version_id >= curr_id:
                req_error = 'Please choose a valid version. chosen %s: current %s' %(version_id, self.current_id())
        except Exception, e:
            req_error = 'Please choose a valid version. %s' %e

        # bail out on error 
        if req_error is not None:
            self.addPortalStatusMessage(req_error)
            raise Redirect(view_url)

        # preserve history
        old_history = IWikiHistory(self.context)

        # actually do the revert
        self.pr.revert(self.context, version_id)

        # XXX This message is used by the CMFEditions gunk. Looks like
        # I have to translate *and* convert to ascii before saving? Icky.
        message = "Rolled back to %s" % translate(
            self.version_title(version_id, rollback=True))
        message = message.encode('ascii', 'ignore')
        if self.pr.supportsPolicy(self.context, 'version_on_revert'):
            self.pr.save(obj=self.context, comment=message)
        reverter = get_member(self.context)
        event = ObjectModifiedEvent(self.context)
        alsoProvides(event, IReversionEvent)
        reversion_info = dict(reversion_message=message,
                              old_history=old_history.annot,
                              rollback_author=reverter)
        event.__dict__.update(reversion_info)
        notify(event)

        # send user to the view page 
        self.addPortalStatusMessage(message)
        self.redirect(view_url)


class WikiVersionCompare(WikiVersionView):

    @instance.memoizedproperty
    def versions(self):
        versions = self.request.form.get('version_id')
        req_error = None
        if not versions or not isinstance(versions, list) or len(versions) < 2:
            req_error = _(u'version_error_choose_two',
                          u'Please choose the two versions you would like to compare.')
        elif len(versions) > 2:
            req_error = _(u'version_error_too_many',
                          u'Please choose only two versions to compare.')
        if not req_error:
            versions.sort()
            old_version_id, new_version_id = self.sort_versions(*versions)
            try:
                old_version = self.get_version(old_version_id)
                new_version = self.get_version(new_version_id)
            except ArchivistRetrieveError:
                req_error = _(u'version_invalid_id',
                              u'Please choose a valid version.')
            
        if req_error:
            # redirect to input page on error
            self.addPortalStatusMessage(req_error)
            raise Redirect('%s/history' % self.context.absolute_url())
        
        return dict(old=(old_version_id, old_version),
                    new=(new_version_id, new_version))

    def handle_diff(self):
        self.old_version_id, self.old_version = self.versions['old']
        self.new_version_id, self.new_version = self.versions['new']
        old_page = self.get_page(self.old_version_id)
        new_page = self.get_page(self.new_version_id)
        binary_error = u'Comparison not possible: %s is a binary file.'
        old = new = None
        try:
            old = unicode(old_page.EditableBody(), 'utf-8')
        except UnicodeDecodeError:
            self.html_diff = binary_error % self.translate(
                self.version_title(self.old_version_id))
        try:
            new = unicode(new_page.EditableBody(), 'utf-8')
        except UnicodeDecodeError:
            self.html_diff = binary_error % self.translate(
                self.version_title(self.new_version_id))
        if None not in (new, old):
            self.html_diff = htmldiff2.htmldiff(old, new)
        self.old_next_enabled = self.old_version_id + 1 < self.new_version_id
        self.old_prev_enabled = self.old_version_id > 0
        self.new_next_enabled = self.new_version_id < self.current_id() 
        self.new_prev_enabled = self.old_next_enabled

    def sort_versions(self, v1, v2):
        """
        Return older_version, newer_version
        """

        v1 = int(v1)
        v2 = int(v2)
        if v1 > v2:
            return v2, v1
        else:
            return v1, v2

    def __call__(self, *args, **kwargs):
        self.handle_diff()
        return super(BaseView, self).__call__(*args, **kwargs)


def wiki_page_edited(page, event):
    history = IWikiHistory(page)
    if IReversionEvent.providedBy(event):
        return history.new_history_item(message=event.reversion_message,
                                        history=event.old_history,
                                        reversion=True,
                                        author=event.rollback_author)
    return history.new_history_item(author=get_member(page))

annot_key = 'opencore.nui.wiki.wikihistory'

class AnnotationCachedWikiHistory(object):
    """adapter for wiki pages to provide history information

       The data is stored on the current version of each page. When a new
       version is created (edit is made), the cache information is copied from
       the previous version to the current one"""

    implements(IWikiHistory)

    def __init__(self, context):
        self.context = context
        annot = IAnnotations(context)
        wiki_annot = annot.get(annot_key, None)
        if wiki_annot is None:
            wiki_annot = IOBTree()
            annot[annot_key] = wiki_annot
        self.annot = wiki_annot

    def __iter__(self):
        # Gotcha: We iterate from highest id (most recent) to low (oldest).
        for version_id in reversed(self.annot.keys()):
            yield self.annot[version_id]

    def __len__(self):
        # XXX why not just len(self.annot)?
        return len(self.annot.keys())

    def __getitem__(self, version_id):
        if version_id < 0:
            # Support list-like negative indexing.
            keys = sorted(self.annot.keys())
            version_id = keys[version_id]
        return self.annot[version_id]

    def new_history_item(self, message=None, reversion=False, history=None,
                         author=None):
        """This will add a new history item to the history cache
        stored on the page.  WARNING: This method assumes it is being
        called _during_ the request when the revision is actually
        taking place.  It is not meant to be used after the fact, to
        synchronize with the existing history information in the
        portal_repository.  Please use the resync_history_cache method
        for that purpose.
        """
        page = self.context
        try:
            repo = getToolByName(page, 'portal_repository')
            first_item = repo.getHistory(page, countPurged=False)[0]
        except ArchivistRetrieveError:
            if not page.getText():
                # @@ hack for portal factory :(
                return
            new_version_id = 0
        else:
            new_version_id = first_item.version_id 
            if not reversion:
                new_version_id = first_item.version_id + 1
                
            if not history:
                history = IWikiHistory(first_item.object)
                self.annot.update(dict(history.annot))
                history.annot.clear()
            else:
                self.annot.update(dict(history))

        if message is None:
            message = ILastModifiedComment(page).getValue()

        if author is None:
            author = ILastModifiedAuthorId(page)
            
        new_history_item = dict(
            # XXX We should store the historical title in here too.
            version_id=new_version_id,
            comment=message,
            author=author,
            modification_date=DateTime(), # now
            )

        self.annot[new_version_id] = new_history_item

    def resync_history_cache(self):
        """
        Synchronizes the history cache stored on the page object w/
        the canonical history that is stored in the portal_repository,
        overwriting whatever was already in the cache.
        """
        page = self.context
        new_cache = IOBTree()
        repo = getToolByName(page, 'portal_repository')
        real_history = repo.getHistory(page, countPurged=False)
        # most recent is first, need to reverse
        for revision in reversed(real_history):
            sys_md = revision.sys_metadata
            version_id = revision.version_id
            new_history_item = dict(
                version_id=version_id,
                comment=revision.comment,
                author=sys_md.get('principal'),
                modification_date=DateTime(sys_md.get('timestamp'))
                )
            new_cache[version_id] = new_history_item
        # we've populated the new cache, now write it back to the
        # storage
        annot = IAnnotations(page)
        annot[annot_key] = new_cache
        self.annot = annot[annot_key]


class WikiPageVersionMigrate(BrowserView):
    @post_only(raise_=True)
    def migrate(self):
        pr = getToolByName(self, 'portal_repository')
        result = utils.cache_history(self.context, pr)
        if result:
            return "%s entries migrated" %result
        else:
            return "Nothing migrated: result is %s" %result

class RedirectView(WikiVersionView):
    def __call__(self):
        current = self.current_id()
        previous = self.previous_id(current)
        if previous < 0:
            # if there have been no edits, just redirect to the page itself
            # XXX TODO: i18nify this psm!
            self.addPortalStatusMessage("There have been no edits to this page since it was created.")
            return self.redirect(self.context.absolute_url())
        url = "%s/version_compare?version_id=%d&version_id=%d" % (self.context.absolute_url(), current, previous)    
        return self.redirect(url)
