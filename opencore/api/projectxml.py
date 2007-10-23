from Products.Five import BrowserView

class MemberXML(BrowserView):

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        response = request.RESPONSE
        response.setHeader('Content-Type',"application/xml")

    def team(self):
        return self.context.getTeams()[0]
    
    def members(self):
        return self.team().getFolderContents(None,batch=True,full_objects=True)
