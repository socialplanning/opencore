from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import transaction_note
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.interfaces.event import AfterProjectAddedEvent #, AfterSubProjectAddedEvent
from opencore.nui.base import BaseView, button
from zExceptions import BadRequest
from zExceptions import Redirect
from zope import event
from topp.utils.pretty_date import prettyDate

        
class ProfileView(BaseView):

    def activity(self, max=5):
        """Returns a list of dicts describing each of the `max` most recently
        modified wiki pages for the viewed user."""
        catalog = getToolByName(self.context, 'portal_catalog')
        query = dict(Creator=self.viewedmember().getId(), portal_type='Document', sort_on='modified', sort_order='reverse')
        brains = catalog.searchResults(**query)
        items = []
        for brain in brains[:max]:
            items.append({'title': brain.Title, 'url': brain.getURL(), 'date': prettyDate(brain.getRawCreation_date())})
        return items

    def viewingself(self):
        return self.viewedmember() == self.loggedinmember
      

class ProfileEditView(ProfileView):

    def handle_request(self):
        pass

    def handle_form(self):
        usr = self.viewedmember()
        portrait = self.request.form.get('portrait')
        task = self.request.form.get('task')
        if task == 'upload':
            usr.setPortrait(portrait)
            return { 'oc-profile-avatar' : '<div class=oc-avatar id=oc-profile-avatar><img src="%s" /><fieldset class=oc-expander style=clear: left;> <legend class=oc-legend-label><!-- TODO --><a href=# class=oc-expander-link>Change image</a></legend><div class=oc-expander-content><input type=file size=14 /><br /><button type=submit name=task value=oc-profile-avatar_uploadAndUpdate>Update</button> or <a href=#>remove image</a></div></fieldset></div>' % portrait.filename}

        # task == 'update'
        for field, value in self.request.form.items():
            mutator = 'set%s' % field.capitalize()
            mutator = getattr(usr, mutator, None)
            if mutator:
                mutator(value)

        return self.redirect('profile')
