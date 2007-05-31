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

    def info(self):
        """Returns profile information in a dict for easy template access."""
        usr = self.vieweduser()
        portrait = usr.getProperty('portrait', None)
        portraitURL = portrait and portrait.absolute_url()
        return dict(membersince = prettyDate(usr.getRawCreation_date()),
                    lastonline  = prettyDate(usr.getLast_login_time()),
                    portraitURL = portraitURL,
                    )


class ProfileEditView(BaseView):

    @button('update')
    def handle_request(self):
        self.context.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if not self.errors:
            self.context.processForm(REQUEST=self.request)
            self.redirect(self.context.absolute_url())
