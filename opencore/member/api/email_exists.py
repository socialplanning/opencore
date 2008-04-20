from opencore.browser.base import BaseView
import urllib

class EmailExistsView(BaseView):
    """
    Simple view that provides a RESTful API for determining whether a
    given email address is in use on the site.
    """
    def email_exists(self):
        """
        Expects an 'email' entry in the request form.  Returns a 200
        response if the email is being used, a 404 otherwise.
        """
        email = self.request.form.get('email')
        response = self.request.response
        response.setHeader('Content-Type', 'text/xml')
        if email is not None:
            email = urllib.unquote(email)
            mbtool = self.get_tool('membrane_tool')
            if len(mbtool.unrestrictedSearchResults(getEmail=email)) > 0:
                content = "<email>%s</email>" % email
                response.setHeader('Content-Length', len(content))
                return content

        response.setStatus(404)
        content = "<email />"
        response.setHeader('Content-Length', len(content))
        return content
