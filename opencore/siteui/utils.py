"""
Browser view utility methods.
"""

from browserview import Base as BrowserView

APP_HEADER = 'HTTP_X_OPENPLANS_APPLICATION'

class JSConditions(BrowserView):
    """
    Methods invoked by the condition expressions in the
    portal_javascripts tool.
    """
    def in_app(self, appname):
        realappname = self.request.get(APP_HEADER, '')
        return appname == realappname
