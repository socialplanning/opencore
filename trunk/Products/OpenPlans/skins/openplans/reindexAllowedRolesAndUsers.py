## Script (Python) "reindexAllowedRolesAndUsers"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Get text for the project role for current member
##
from Products.CMFCore.utils import getToolByName
cat = getToolByName(context, 'portal_catalog')
cat.reindexIndex('allowedRolesAndUsers', context.REQUEST)

