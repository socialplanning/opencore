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

    defaultPortraitURL = '++resource++img/default-portrait.jpg'

    def info(self):
        """Returns profile information in a dict for easy template access."""
        usr = self.viewedmember()
        portrait = usr.getProperty('portrait', None)
        portraitURL = portrait and portrait.absolute_url() or self.defaultPortraitURL
        return dict(membersince = prettyDate(usr.getRawCreation_date()),
                    lastonline  = prettyDate(usr.getLast_login_time()),
                    portraitURL = portraitURL,
                    )

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

    @button('update')
    def handle_request(self):
        self.context.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if not self.errors:
            self.context.processForm(REQUEST=self.request)
            self.redirect(self.context.absolute_url())
