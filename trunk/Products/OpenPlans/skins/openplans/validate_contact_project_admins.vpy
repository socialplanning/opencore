## Controller Script Python "validate_contact_project_admins"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state  
##bind subpath=traverse_subpath
##parameters=send_from_address='', subject='', message=''
##title=validates the email adresses

plone_utils = context.plone_utils
request = context.REQUEST

if request.form.has_key('send_from_address'):
    if not send_from_address:
        state.setError('send_from_address',
                       'Please submit an email address.',
                       'email_required')
    if not plone_utils.validateEmailAddresses(send_from_address):
        state.setError('send_from_address',
                       'Please submit a valid email address.',
                       'email_required')

if not subject:
    state.setError('subject',
                   'Please include a message subject.',
                   'subject_required')

if not message:
    state.setError('message',
                   'Please include your message to the project administrators.',
                   'message_required')

if state.getErrors():
    return state.set(status='failure',
                     portal_status_message='Please correct the indicated errors.')
else:
    return state
