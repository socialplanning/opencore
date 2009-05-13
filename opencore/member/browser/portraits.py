from Products.MimetypesRegistry.mime_types import magic
from opencore.browser.base import BaseView
import os.path
import DateTime

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
        member_portrait_thumb = getattr(self.viewedmember(), thumbnail_property, None)
        if member_portrait_thumb is not None:
            data = member_portrait_thumb.data
            modified = member_portrait_thumb.bobobase_modification_time()
            content_type = member_portrait_thumb.content_type
        else:
            default_thumb = getattr(self, default_thumb)
            path = self.context.restrictedTraverse(default_thumb).context.path
            file = open(path, 'rb')
            modified = DateTime.DateTime(os.path.getmtime(path))
            data = file.read()
            content_type = magic.guessMime(data)
            file.close()

        self.response.setHeader('Content-Type', content_type)
        modified = modified.toZone('GMT')
        self.response.setHeader('Last-Modified', modified.rfc822())
        # DateTime can be added to a number of days (not seconds!)
        self.response.setHeader('Expires', (DateTime.DateTime() + 1).rfc822())
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
