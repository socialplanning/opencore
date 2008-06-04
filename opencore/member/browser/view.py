from DateTime import DateTime
from Products.AdvancedQuery import Eq
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.remember.interfaces import IReMember
from opencore.browser.base import BaseView, _
from opencore.browser.formhandler import OctopoLite, action
from opencore.interfaces.event import MemberModifiedEvent
from topp.utils.pretty_date import prettyDate
from zope.app.event.objectevent import ObjectModifiedEvent
from zope.component import getMultiAdapter
from zope.event import notify
import urllib

class ProfileView(BaseView):

    field_snippet = ZopeTwoPageTemplateFile('field_snippet.pt')
    member_macros = ZopeTwoPageTemplateFile('member_macros.pt') 


    # XXX this seems to be called twice when i hit /user/profile 
    #     or /user/profile/edit ... why is that?
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        self.public_projects = []
        self.private_projects = []

    def mship_proj_map(self):
        """map from team/project id's to {'mship': mship brain, 'proj': project brain}
        maps. relies on the 1-to-1 mapping of team ids and project ids."""
        mships = self.mship_brains_for(self.viewedmember())
        mp_map = {}
        for mship in mships:
            team = mship.getPath().split('/')[-2]
            mp_map[team] = dict(mship=mship)

        for proj in self.project_brains_for(self.viewedmember()):
            mp_map[proj.getId]['proj'] = proj
        # XXX
        # the mship and the corresponding project should have the same
        # visibility permissions, such that the two queries yield
        # len(projects) == len(mships).
        # there could be a discrepancy, however (caused by not putting
        # placeful workflow on the teams). the following will filter
        # out items in the map for which the logged in member cannot
        # view both the mship and the corresponding project of the
        # viewed member.
        mp_copy = dict(mp_map)  # XXX why do we need a copy here?
        for (k, v) in mp_copy.items():
            if not v.has_key('proj'):
                del mp_map[k]

        return mp_map


    def populate_project_lists(self):
        for (_, m) in self.mship_proj_map().items():
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
        query =  Eq('lastModifiedAuthor', memberid)
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


class ProfileEditView(ProfileView, OctopoLite):

    portrait_snippet = ZopeTwoPageTemplateFile('portrait-snippet.pt')
    template = ZopeTwoPageTemplateFile('profile-edit.pt')

    def has_invitations(self):
        """check whether the member has any pending project
        invitations to manage"""
        member = self.loggedinmember
        pending_mships = self.catalog(portal_type='OpenMembership',
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
        validation_failed = False
        form = self.request.form
        
        # deal with portrait first
        portrait = form.get('portrait')
        if portrait:
            if self.check_portrait(member, portrait):
                del form['portrait']
            else:
                validation_failed = True

        # Do validation from any plugins.
        viewlet_mgr = getMultiAdapter((self.context, self.request, self),
                                      name='opencore.profile_edit_viewlets')
        if not hasattr(viewlet_mgr, 'viewlets'):
            viewlet_mgr.update()
        for viewlet in viewlet_mgr.viewlets:
            if hasattr(viewlet, 'validate'):
                errors = viewlet.validate()
                for key, msg in errors.items():
                    validation_failed = True
                    self.addPortalStatusMessage(msg)

        if validation_failed:
            return

        # Now allow any plugins to save state.
        for viewlet in viewlet_mgr.viewlets:
            if hasattr(viewlet, 'save'):
                viewlet.save()

        # now deal with the rest of the fields via archetypes mutators.
        for field, value in form.items():
            mutator = 'set%s' % field.capitalize() # Icky, fragile.
            mutator = getattr(member, mutator, None)
            if mutator is not None:
                mutator(value)
        self.user_updated()

        notify(ObjectModifiedEvent(member))
        #XXX some handlers listen to a specific event, since the object modified
        #one can be called multiple times
        notify(MemberModifiedEvent(member))
    
        member.reindexObject()
        self.template = None
        return self.redirect('profile')
        
    def user_updated(self): # TODO
        """callback to tell taggerstore a user updated (possibly) taggifiable
        fields. something like a POST to /taggerstore/."""
        pass

