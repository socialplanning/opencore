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
        """appends timestamp to portrait url to circumvent browser cache"""
        return '%s?%s' % (self.viewed_member_info.get('portrait_url'),
                          datetime.now().strftime('%s'))


class ProfileEditView(ProfileView):

    portrait_snippet = ZopeTwoPageTemplateFile('portrait-snippet.pt')

    def handle_form(self):
        usr = self.viewedmember()
        portrait = self.request.form.get('portrait')
        mode = self.request.form.get('mode')
              
        # TODO resize portrait if necessary

        # the only asynchronous form behavior is for change portrait
        if mode == 'async':
            usr.setPortrait(portrait)
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


    #TODO handle_remove_image


    def user_updated(self): # TODO
        """callback to tell taggerstore a user updated (possibly) taggifiable
        fields. something like a POST to /taggerstore/."""
        pass
