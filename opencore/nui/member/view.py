from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import transaction_note
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.nui.base import BaseView, button
from zExceptions import BadRequest
from zExceptions import Redirect
from zope import event
from topp.utils.pretty_date import prettyDate

        
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

        # use a list comprehension and a function?
        items = []
        for brain in brains:
            items.append({'title': brain.Title, 'url': brain.getURL(), 'date': prettyDate(brain.getRawCreation_date())})
        return items

    def viewingself(self):
        return self.viewedmember() == self.loggedinmember


class ProfileEditView(ProfileView):

    portrait_snippet = ZopeTwoPageTemplateFile('portrait-snippet.pt')

    # TODO fix ajax w/ nickyg
    # TODO resize portrait
    def handle_form(self):
        usr = self.viewedmember()
        portrait = self.request.form.get('portrait')
        mode = self.request.form.get('mode')
              
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
    
            usr.reindexObject()
            return self.redirect('profile')
