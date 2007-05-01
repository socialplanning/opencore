## Script (Python) "member_search"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=query, exact_match=False
##title=convenience method for searching member catalog from page templates
##
if not query:
    return

from Products.CMFCore.utils import getToolByName
mbtool = getToolByName(context, 'membrane_tool')

if not exact_match:
    textindexes = {'getEmail': 0,
                   'getFullname': 0,
                   'getUserName': 0}
    for key, value in query.items():
        if key in textindexes:
            # add glob characters
            tokens = value.strip().split()
            tokens = ["%s*" % token for token in tokens]
            value = " ".join(tokens)
            query[key] = value

brains = mbtool(**query)
#mems = [b.getObject() for b in brains]
#return mems
return brains
