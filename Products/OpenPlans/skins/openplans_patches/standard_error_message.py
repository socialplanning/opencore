## Script (Python) "standard_error_message"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=**kwargs
##title=Dispatches to relevant error view
##

## by default we handle everything in 1 PageTemplate.
#  you could easily check for the error_type and
#  dispatch to an appropriate PageTemplate.

# Check if the object is traversable, if not it might be a view, get its parent
# because we need to render the error on an actual content object
from AccessControl import Unauthorized
try:
    while not hasattr(context.aq_explicit, 'restrictedTraverse'):
        context = context.aq_parent
except (Unauthorized, AttributeError):
    context = context.portal_url.getPortalObject()

error_type=kwargs.get('error_type', None)
error_message=kwargs.get('error_message', None)
error_log_url=kwargs.get('error_log_url', None)
error_tb=kwargs.get('error_tb', None)
error_traceback=kwargs.get('error_traceback', None)
error_value=kwargs.get('error_value', None)

error_page_view=context.restrictedTraverse('error')

error_page=error_page_view(error_type=error_type,
                           error_message=error_message,
                           error_tb=error_tb,
                           error_value=error_value)

# Force the error page content type to text/html.  We *sometimes* were
# getting 'application/xml', which is wrong; and if/when we have
# invalid markup in that page, it causes firefox to display useless
# (to the average user) xml parse errors instead of our error page.
context.REQUEST.RESPONSE.setHeader('Content-Type', 'text/html; charset=utf8')

return error_page
