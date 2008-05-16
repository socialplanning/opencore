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

    def _portrait_thumb(self, thumbnail_property, default_thumb='defaultPortraitThumbURL'):
        """Provides a single location to pull the user's portrait from. 
        Same as above, but returns the thumbnail.""" 
        try:
            member_portrait_thumb = getattr(self.viewedmember(), thumbnail_property)
            data = member_portrait_thumb.data
        except AttributeError:
            default_thumb = getattr(self, default_thumb)
            file = open(self.context.restrictedTraverse(default_thumb).context.path, 'rb') 
            data = file.read()
            file.close()

        content_type = magic.guessMime(data)
        self.response.setHeader('Content-Type', content_type)
        return data

    def portrait_thumb(self):
        return self._portrait_thumb('portrait_thumb',
                                    default_thumb='defaultPortraitThumbURL')

    def portrait_square_thumb(self):
        return self._portrait_thumb('portrait_square_thumb',
                                    default_thumb='defaultPortraitSquareThumbURL')

    def portrait_square_fifty_thumb(self):
        return self._portrait_thumb('portrait_square_fifty_thumb',
                                    default_thumb='defaultPortraitSquareFiftyThumbURL')
