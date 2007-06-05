## Script (Python) "pwreset_constructURL.py"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##title=Create the URL where passwords are reset
##parameters=randomstring
host = container.absolute_url()
return "%s/reset-password?key=%s" % (host, randomstring)
