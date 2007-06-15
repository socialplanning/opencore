 wiki ui
=========

    >>> page_id = self.portal.projects.p1.getDefaultPage()
    >>> page = getattr(self.portal.projects.p1, page_id)

Registrations
=============

Test wiki page registrations::

    >>> page.restrictedTraverse('@@view')
    <...SimpleViewClass from ...wiki/wiki-view.pt object at ...>
    
    >>> page.restrictedTraverse('@@wiki_macros')
    <...SimpleViewClass ...wiki/wiki_macros.pt object at ...>
    
    >>> page.restrictedTraverse('@@edit')
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access '@@edit' in this context

Test wiki history registrations::

    >>> page.restrictedTraverse('history')
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'history' in this context

    >>> page.restrictedTraverse('version')
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'version' in this context
    

    >>> page.restrictedTraverse('version_compare')
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'version_compare' in this context


Test wiki attachment registrations::

    >>> page.restrictedTraverse('@@updateAtt')
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access '@@updateAtt' in this context

    >>> page.restrictedTraverse('@@createAtt')    
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access '@@createAtt' in this context

    >>> page.restrictedTraverse('@@deleteAtt')    
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access '@@deleteAtt' in this context

Test logged in user::

    >>> self.loginAsPortalOwner()

Test wiki page registrations (logged in)::

    >>> page.restrictedTraverse('@@view')
    <...SimpleViewClass from ...wiki/wiki-view.pt object at ...>
    
    >>> page.restrictedTraverse('@@wiki_macros')
    <...SimpleViewClass ...wiki/wiki_macros.pt object at ...>
    
    >>> page.restrictedTraverse('@@edit')
    <...SimpleViewClass ...wiki/wiki-edit.pt object at ...>

Test wiki history registrations (logged in)::

    >>> page.restrictedTraverse('history')
    <Products.Five.metaclass.SimpleViewClass from ...wiki-history.pt object at ...>

    >>> page.restrictedTraverse('version')
    <Products.Five.metaclass.SimpleViewClass ...wiki/wiki-previous-version.pt object at ...>

    >>> page.restrictedTraverse('version_compare')
    <Products.Five.metaclass.SimpleViewClass from ...wiki-version-compare.pt object at ...>

    
Test wiki attachment registrations (logged in)::

    >>> page.restrictedTraverse('@@updateAtt')
    <Products.Five.metaclass.AttachmentView object at ...>

    >>> page.restrictedTraverse('@@createAtt')    
    <Products.Five.metaclass.AttachmentView object at ...>

    >>> page.restrictedTraverse('@@deleteAtt')    
    <Products.Five.metaclass.AttachmentView object at ...>

Test actually creating, editing, deleting an attachment::

     >>> import os
     >>> import hmac
     >>> import sha
     >>> import base64
     >>> import re
     >>> from urllib import quote
     >>> secret_file_name = os.environ.get('TOPP_SECRET_FILENAME', '')
     >>> if not secret_file_name:
     ...    secret_file_name = os.path.join(os.environ.get('INSTANCE_HOME'), 'secret.txt')
     
     >>> len(secret_file_name) > 0
     True
     >>> os.path.exists(secret_file_name)
     True
     >>> f = open(secret_file_name)
     >>> secret = f.readline().strip()
     >>> f.close()
     >>> len(secret) > 0
     True

     Create attachment
     >>> from opencore.nui.wiki import view as v
     >>> request = self.portal.REQUEST
     >>> view = v.AttachmentView(page, request)
     >>> view = view.__of__(page)
     >>> view.createAtt()
     "{'status' : 'failed' }\n"
     >>> view.request['attachmentTitle'] = 'secret'
     >>> class tempfile(file):
     ...     def __init__(self, filename):
     ...         self.filename = filename 
     ...         file.__init__(self, filename)
     >>> tfile = tempfile(secret_file_name)
     >>> view.request['attachmentFile'] = tfile
     >>> view.request['attachment_id'] = 'secret.txt'
     >>> view.createAtt()
     "{status: 'success',...
     >>> newatt = view.context._getOb('secret.txt')
     >>> newatt
     <FileAttachment at /plone/projects/p1/project-home/secret.txt>
     >>> newatt.Title()
     'secret'


Now let's try to delete.  Try the error case::

     >>> request.set('attachment_id', '')
     >>> request.set('attachmentTitle', '')
     >>> request.set('attachmnetFile', '')

     Again, raising an AttributeError
     Maybe we should return an error message instead
     >>> view.deleteAtt()
     Traceback (most recent call last):
     ...
     AttributeError

     Set valid attachment request variables, and it should work
     >>> request.set('attachment_id', 'secret.txt')
     >>> request.set('attachmentFile', tfile)
     >>> request.set('attachmnetTitle', 'new title')
     >>> view.deleteAtt()
     '<!-- deleted -->\n'


If we create an attachment with no title, the title should be the id::
     >>> tfile = tempfile(secret_file_name)
     >>> view.request['attachmentFile'] = tfile
     >>> response = view.createAtt()
     >>> "status: 'success'" in response
     True
     >>> newatt = view.context._getOb('secret.txt')
     >>> newatt
     <FileAttachment at /plone/projects/p1/project-home/secret.txt>
     >>> newatt.Title()
     'secret.txt'


Test update attachment::
     >>> view.attachmentSnippet()
     '...secret.txt...

     Reset attachment request variables
     >>> request.set('attachment_id', '')
     >>> request.set('attachmentTitle', '')
     >>> request.set('attachmnetFile', '')

Check error case (should it raise an error? error message instead?)::
     >>> view.updateAtt()
     Traceback (most recent call last):
     ...
     AttributeError

     Set valid attachment request variables
     >>> request.set('attachment_id', 'secret.txt')
     >>> request.set('attachmentFile', tfile)
     >>> request.set('attachmnetTitle', 'new title')

Try again, should work great now::
     (uhh, what do we expect to get back? looks like a form?)
     >>> response = view.updateAtt()
     >>> '<form method="post"' in response
     True
     >>> 'secret.txt' in response
     True



Now let's exercise some version compare stuff

Verify that a redirect is raised on invalid input

Set up the right view
     >>> view = self.portal.unrestrictedTraverse('projects/p1/project-home/version_compare')
     >>> view
     <Products.Five.metaclass.SimpleViewClass from ...wiki-version-compare.pt object at ...>

Call it with no arguments
     >>> response = view()
     Traceback (most recent call last):
     ...
     Redirect: http://nohost/plone/projects/p1/project-home/history
     >>> 'You did not check any versions in the version compare form' in view.portal_status_message
     True

Try it with just one argument
     >>> view.request.set('version_id', '0')
     >>> response = view()
     Traceback (most recent call last):
     ...
     Redirect: http://nohost/plone/projects/p1/project-home/history
     >>> 'You did not check enough versions in the version compare form' in view.portal_status_message
     True

Try with 2 arguments, but the versions don't exist
     >>> view.request.set('version_id', ['0', '1'])
     >>> response = view()
     Traceback (most recent call last):
     ...
     Redirect: http://nohost/plone/projects/p1/project-home/history
     >>> 'Invalid version specified' in view.portal_status_message
     True

Try with more than 2 versions
     >>> view.request.set('version_id', ['0', '1', '2'])
     >>> response = view()
     Traceback (most recent call last):
     ...
     Redirect: http://nohost/plone/projects/p1/project-home/history
     >>> 'You may only check two versions in the version compare form' in view.portal_status_message
     True

Now edit 2 pages, so we can try a valid compare later
     >>> view.request.set('version_id', ['0', '1'])
     >>> repo = view.get_tool('portal_repository')
     >>> page.processForm(values=dict(text='some new text'))
     >>> repo.save(page, comment='new comment')
     >>> page.processForm(values=dict(text='some even newer text'))
     >>> repo.save(page, comment='newest comment')

Now we should get a valid response
     >>> response = view()
