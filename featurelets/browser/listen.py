from Products.Five import BrowserView

class ListenConfigView(BrowserView):
    """
    View object that renders the configuration page for the listen
    featurelet.
    """
    def __init__(self, context, request):
        self._context = (context,)
        self.request = request

    def __call__(self):
        return "SUCCESS!"
