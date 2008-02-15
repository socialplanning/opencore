from DateTime import DateTime
from Products.AdvancedQuery import Eq
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from datetime import datetime
from datetime import timedelta
from opencore.browser.base import BaseView, _
from opencore.browser.formhandler import OctopoLite, action
from opencore.geocoding.view import get_geo_reader
from opencore.geocoding.view import get_geo_writer
from opencore.interfaces.message import ITransientMessage
from plone.memoize.view import memoize as req_memoize
from topp.utils.pretty_date import prettyDate
from urlparse import urlsplit
from zope.app.event.objectevent import ObjectModifiedEvent
from zope.event import notify


class ProfileView(BaseView):

    field_snippet = ZopeTwoPageTemplateFile('field_snippet.pt')
    member_macros = ZopeTwoPageTemplateFile('member_macros.pt') 

    # XXX this seems to be called twice when i hit /user/profile 
    #     or /user/profile/edit ... why is that?
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        self.public_projects = []
        self.private_projects = []

    def populate_project_lists(self):
        mship_proj_map = self.mship_proj_map()
        for (_, m) in mship_proj_map.items():
            mship = m['mship']
            proj = m['proj']
            if mship.review_state == 'private' or proj.review_state == 'closed':
                self.private_projects.append(proj)
            else:
                self.public_projects.append(proj)

            sortfunc = lambda x: x.Title.lower()
            self.private_projects.sort(key=sortfunc)
            self.public_projects.sort(key=sortfunc)


    def activity(self, max=10):
        """Returns a list of dicts describing each of the `max` most recently
        modified wiki pages for the viewed user."""
        memberid = self.viewed_member_info['id']
        query = Eq('Creator', memberid) | Eq('lastModifiedAuthor', memberid)
        query &= Eq('portal_type', 'Document') #| Eq('portal_type', 'OpenProject')
        brains = self.catalog.evalAdvancedQuery(query, (('modified', 'desc'),)) # sort by most recent first ('desc' means descending)
        brains = brains[:max] # there appears to be no way to specify the max in the query

        def dictify(brain):
            d = dict(title = brain.Title,
                     url   = brain.getURL(),
                     date  = prettyDate(DateTime(brain.ModificationDate)))

            try:
                path = brain.getPath().split('/')
                # get index of the projects folder
                pfindex = path.index('projects') # TODO don't hard code projects folder
                projid = path[pfindex + 1]
                projpath = '/'.join(path[:pfindex+2])
                projmeta = self.catalog.getMetadataForUID(projpath)
                d['project'] = projmeta['Title']

                # get index of the right-most '/'
                rslashindex = d['url'].rindex('/')
                d['projurl'] = d['url'][:rslashindex]

            except ValueError:
                # this page brain must not be inside a project
                d.update(project=None, projurl=None)
            except KeyError:
                # this page brain must not be inside a project
                d.update(project=None, projurl=None)

            return d

        return [dictify(brain) for brain in brains]

    def viewingself(self):
        return self.viewedmember() == self.loggedinmember

    def mangled_portrait_url(self):
        """When a member changes her portrait, her portrait_url remains the same.
        This method appends a timestamp to portrait_url to trick the browser into
        fetching the new image instead of using the cached one which could be --
        and always will be in the ajaxy-change-portrait case -- out of date.
        P.S. This is an ugly hack."""
        portrait_url = self.viewed_member_info.get('portrait_url')
        if portrait_url == self.defaultPortraitURL:
            return portrait_url
        timestamp = str(DateTime()).replace(' ', '_')
        return '%s?%s' % (portrait_url, timestamp)

    def trackbacks(self):
        self.msg_category = 'Trackback'

        tm = ITransientMessage(self.portal)
        mem_id = self.viewed_member_info['id']
        msgs = tm.get_msgs(mem_id, self.msg_category)

        timediff = datetime.now() - timedelta(days=60)
        old_messages = [(idx, value) for (idx, value) in msgs if value['time'] < timediff]
        for (idx, value) in old_messages:
            tm.pop(mem_id, self.msg_category, idx)
        if old_messages:
            # We've removed messages, so we should refresh the list
            msgs = tm.get_msgs(mem_id, self.msg_category)

        # We want to insert the indexes into the values so that we can properly address them for deletion
        addressable_msgs = []
        for (idx, value) in msgs:
            if 'excerpt' not in value.keys():
                tm.pop(mem_id, self.msg_category, idx)
                value['excerpt'] = ''
                tm.store(mem_id, self.msg_category, value)

                # XXX TODO: We don't want to display escaped HTML entities,
                # eg. if the comment text contains "I paid &#8364;20
                # for mine" we want the user to see the euro symbol,
                # not the entity code.  But we don't want to just
                # throw them away either.  We could leave the data
                # alone and use "structure" in the template; but then
                # we're assuming the data is safe, and it's only as
                # trustworthy as the openplans user.  Below is some
                # code that just throws the entities (and all HTML)
                # away.  Maybe we could convert entities to unicode
                # prior to or instead of calling detag?  Can do that
                # using Beautiful Soup, see: http://tinyurl.com/28ugnq

#             from topp.utils.detag import detag
#             for k, v in value.items():
#                 if isinstance(v, basestring):
#                     value[k] = detag(v)
            value['idx'] = 'trackback_%d' % idx
            value['close_url'] = 'trackback-delete?idx=%d' % idx
            value['pub_date']    = prettyDate(value['time'])
            addressable_msgs.append(value)

        return addressable_msgs

    @property
    def geo_info(self):
        """geo information for display in forms;
        takes values from request, falls back to existing member info
        if possible."""
        geo = get_geo_reader(self)
        info = geo.geo_info()
        # Override the static map image size. Ugh, sucks to have this in code.
        info['static_img_url'] = geo.location_img_url(width=285, height=285)
        return info

class ProfileEditView(ProfileView, OctopoLite):

    portrait_snippet = ZopeTwoPageTemplateFile('portrait-snippet.pt')
    template = ZopeTwoPageTemplateFile('profile-edit.pt')

    def has_invitations(self):
        """check whether the member has any pending project
        invitations to manage"""
        member = self.loggedinmember
        cat = self.catalogtool
        pending_mships = cat(portal_type='OpenMembership',
                             review_state='pending')
        return bool(pending_mships)

    def check_portrait(self, member, portrait):
        try:
            member.setPortrait(portrait)
        except ValueError: # must have tried to upload an unsupported filetype
            self.addPortalStatusMessage(_(u'psm_choose_image', u'Please choose an image in gif, jpeg, png, or bmp format.'))
            return False
        return True

    @action("uploadAndUpdate")
    def change_portrait(self, target=None, fields=None):
        member = self.viewedmember()
        portrait = self.request.form.get("portrait")

        if not self.check_portrait(member, portrait):
            return

        member.reindexObject('portrait')
        return {
            'oc-profile-avatar' : {
                'html': self.portrait_snippet(),
                'action': 'replace',
                'effects': 'highlight'
                }
            }

    @action("remove")
    def remove_portrait(self, target=None, fields=None):
        member = self.viewedmember()
        member.setPortrait("DELETE_IMAGE")  # AT API nonsense
        member.reindexObject('portrait')
        return {
            'oc-profile-avatar' : {
                'html': self.portrait_snippet(),
                'action': 'replace',
                'effects': 'highlight'
                }
            }

    @action("update")
    def handle_form(self, target=None, fields=None):
        member = self.viewedmember()

        # deal with portrait first
        portrait = self.request.form.get('portrait')
        if portrait:
            if not self.check_portrait(member, portrait):
                return
            del self.request.form['portrait']

        # handle geo stuff
        geo_writer = get_geo_writer(self)
        new_info, locationchanged = geo_writer.save_coords_from_form()
        form = self.request.form
        member.setPositionText(new_info.get('position-text', ''))
        for key in ('position-latitude', 'position-longitude', 'position-text'):
            # we've already handled these, leave the rest for archetypes.
            if form.has_key(key):
                del form[key]

        # now deal with the rest of the fields via archetypes mutators.
        for field, value in form.items():
            mutator = 'set%s' % field.capitalize() # Icky, fragile.
            mutator = getattr(member, mutator, None)
            if mutator is not None:
                mutator(value)
        self.user_updated()

        notify(ObjectModifiedEvent(member))
    
        member.reindexObject()
        self.template = None
        return self.redirect('profile')
        
    def user_updated(self): # TODO
        """callback to tell taggerstore a user updated (possibly) taggifiable
        fields. something like a POST to /taggerstore/."""
        pass


class TrackbackView(BaseView):
    """handle trackbacks"""

    msg_category = 'Trackback'

    def __call__(self):
        # Add a trackback and return a javascript callback
        # so client script knows when it's done and whether it succeeded.
        mem_id = self.viewed_member_info['id']
        tm = ITransientMessage(self.portal)

        if self.viewedmember() != self.loggedinmember:
            return 'OpenCore.submitstatus(false, "Permission denied");'

        # check for all variables
        url = self.request.form.get('commenturl')
        title = self.request.form.get('title')
        blog_name = self.request.form.get('blog_name', 'an unnamed blog')
        comment = self.request.form.get('comment')
        if None in (url, comment):
            msg = (url == None) and "url not provided" or "comment not provided"
            return 'OpenCore.submitstatus(false, "%s")' % msg
        if not title:
            excerpt = comment.split('.')[0]
            title = excerpt[:100]
            if title != excerpt:
                title += '...'

        tm.store(mem_id, self.msg_category, {'url':url, 'title':title, 'blog_name':blog_name, 'excerpt':comment, 'time':datetime.now()})
        return 'OpenCore.submitstatus(true);'


    def delete(self):
        mem_id = self.viewed_member_info['id']

        if urlsplit(self.request['HTTP_REFERER'])[1] != urlsplit(self.siteURL)[1]:
            self.request.response.setStatus(403)
            return 'Cross site deletes not allowed!'

        # XXX todo 
        #     a) move this to @nui.formhandler.post_only 
        #     b) use that
        if self.request['REQUEST_METHOD'] != 'POST':
            self.request.response.setStatus(405)
            return 'Not Post'
        if self.viewedmember() != self.loggedinmember:
            self.request.response.setStatus(403)
            return 'You must be logged in to modify your posts!'

        index = self.request.form.get('idx')
        if index is None:
            self.request.response.setStatus(400)
            return 'No index specified'

        # Do the delete
        tm = ITransientMessage(self.portal)
        tm.pop(mem_id, self.msg_category, int(index))
        # TODO: Make sure this is an AJAX request before sending an AJAX response
        #       by using octopus/octopolite
        return {'trackback_%s' % index: {'action': 'delete'}}

