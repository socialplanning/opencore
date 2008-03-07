from Products.MimetypesRegistry.mime_types import magic
from opencore.browser.base import BaseView

class PortraitsView(BaseView):
    def portrait(self): 
        """Provides a single location to pull the user's portrait from.""" 
        member_portrait = self.viewedmember().getPortrait() 
        if member_portrait: 
            data = member_portrait.data 
        else: 
            file = open(self.context.restrictedTraverse(self.defaultPortraitURL).context.path, 'rb') 
            data = file.read() 
            file.close() 

        content_type = magic.guessMime(data) 
        self.response.setHeader('Content-Type', content_type) 
        return data 

    def portrait_thumb(self): 
        """Provides a single location to pull the user's portrait from. 
        Same as above, but returns the thumbnail.""" 
        try:
            member_portrait_thumb = self.viewedmember().portrait_thumb 
            data = member_portrait_thumb.data 
        except AttributeError:
            file = open(self.context.restrictedTraverse(self.defaultPortraitThumbURL).context.path, 'rb') 
            data = file.read() 
            file.close() 

        content_type = magic.guessMime(data) 
        self.response.setHeader('Content-Type', content_type) 
        return data 
