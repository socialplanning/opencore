from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import transaction_note
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.nui.base import BaseView, button
from zExceptions import BadRequest
from zExceptions import Redirect
from zope import event
from topp.utils.pretty_date import prettyDate
from datetime import datetime

        
class ProfileView(BaseView):

    field_snippet = ZopeTwoPageTemplateFile('field_snippet.pt')

    def activity(self, max=5):
        """Returns a list of dicts describing each of the `max` most recently
        modified wiki pages for the viewed user."""
        query = dict(Creator=self.viewedmember().getId(),
                     portal_type='Document',
                     sort_on='modified',
                     sort_order='reverse',
                     limit=max)
        brains = self.catalog.searchResults(**query)

        def dictify(brain):
            return {'title': brain.Title,
                    'url':   brain.getURL(),
                    'date':  prettyDate(brain.getRawCreation_date())}

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
        timestamp = datetime.now().isoformat()
        return '%s?%s' % (portrait_url, timestamp)


class ProfileEditView(ProfileView):

    portrait_snippet = ZopeTwoPageTemplateFile('portrait-snippet.pt')

    def handle_form(self):
        usr = self.viewedmember()
        portrait = self.request.form.get('portrait')
        mode = self.request.form.get('mode')
              
        # TODO resize portrait if necessary

        if mode == 'async':
            if portrait:
                usr.setPortrait(portrait)
            else: # TODO detect whether to delete more explicitly. currently the
                  # remove portrait button is identical in name and value to the
                  # change portrait button, so this relies on the user not having
                  # clicked browse and selecting an image first. consult egj/nickyg
                usr._delOb('portrait')
            usr.reindexObject()
            return { 'oc-profile-avatar' : self.portrait_snippet()}

        else:
            for field, value in self.request.form.items():
                mutator = 'set%s' % field.capitalize()
                mutator = getattr(usr, mutator, None)
                if mutator:
                    mutator(value)
                self.user_updated()
    
            usr.reindexObject()
            return self.redirect('profile')


    def user_updated(self): # TODO
        """callback to tell taggerstore a user updated (possibly) taggifiable
        fields. something like a POST to /taggerstore/."""
        pass
