## Script (Python) "showEditableBorder"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=template_id=None, allowed_types=None, actions=None
##title=returns whether or not current template displays *editable* border
##

# turn border on all the time

REQUEST=context.REQUEST

if actions is None:
    raise AttributeError, 'You must pass in the filtered actions'
    
if REQUEST.has_key('disable_border'): #short circuit
    return 0
return 1
