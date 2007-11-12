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

Make sure notallowed css class is applied to edit tab
since we don't have permissions to edit::
    >>> html = page.restrictedTraverse('@@view')()
    >>> 'oc-notallowed' in html
    True

Test wiki history registrations::

    >>> page.restrictedTraverse('history')
    <...SimpleViewClass ...wiki-history.pt object at ...>

    >>> page.restrictedTraverse('version')
    <...SimpleViewClass ...wiki/wiki-previous-version.pt object at ...>

    >>> page.restrictedTraverse('version_compare')
    <...SimpleViewClass ...wiki/wiki-version-compare.pt object at ...>

... and permission

    >>> from AccessControl.SecurityManagement import newSecurityManager
    >>> from AccessControl.User import nobody
    >>> newSecurityManager(None, nobody)
    >>> history = page.restrictedTraverse('history')
    >>> unicode(history())
    u'... There are no previous versions...

Test wiki attachment registrations which are not used any more::

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
    >>> from opencore.browser.base import BaseView
    >>> view = BaseView(self.portal, self.portal.REQUEST)
    >>> view.loggedinmember.getId = lambda *a:'whatever'

Test wiki page registrations (logged in)::

    >>> page.restrictedTraverse('@@view')
    <...SimpleViewClass from ...wiki/wiki-view.pt object at ...>
    
    >>> page.restrictedTraverse('@@wiki_macros')
    <...SimpleViewClass ...wiki/wiki_macros.pt object at ...>
    
    >>> page.restrictedTraverse('@@edit')
    <Products.Five.metaclass.WikiEdit object at ...>

Make sure notallowed css class is not applied to edit tab
since we do have permissions to edit::

    >>> html = page.restrictedTraverse('@@view')()
    >>> 'oc-notallowed' in html
    False

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


Attachments
===========

Test actually creating, editing, deleting an attachment::

     >>> import os, hmac, sha, base64, re
     >>> from urllib import quote
     >>> from opencore.auth.SignedCookieAuthHelper import get_secret_file_name
     >>> secret_file_name = get_secret_file_name()
     >>> len(secret_file_name) > 0
     True
     >>> os.path.exists(secret_file_name)
     True
     >>> f = open(secret_file_name)
     >>> secret = f.readline().strip()
     >>> f.close()
     >>> len(secret) > 0
     True

Error case for creating an attachment with no attachment there::

     >>> request = self.portal.REQUEST
     >>> view = page.restrictedTraverse('@@edit')
     >>> view.create_attachment()
     {'An error': ''}

Create an attachment to upload::

     >>> class tempfile(file):
     ...     def __init__(self, filename):
     ...         self.filename = filename 
     ...         file.__init__(self, filename)
     >>> tfile = tempfile(secret_file_name)

     >>> form = {}
     >>> form['attachmentTitle'] = 'secret'
     >>> form['attachmentFile'] = tfile
     >>> request.form = form
     >>> view.create_attachment()
     {...'oc-wiki-attachments'...}
     >>> attachs = view.fileAttachments()
     >>> len(attachs)
     1
     >>> newatt = attachs[0].getObject()
     >>> newatt
     <FileAttachment at /plone/projects/p1/project-home/secret.txt>
     >>> newatt.Title()
     'secret'

Now let's try to delete.  Try the error case::

     >>> request.form = {}

It raises a TypeError for now, but should eventually return an error message instead::

     >>> view.delete_attachment()
     Traceback (most recent call last):
     ...
     TypeError...

Send in valid attachment id and it should work::

     >>> form = {}
     >>> view.delete_attachment(['secret.txt'])
     {'secret.txt_list-item':...'delete'...}

If we create an attachment with no title, the title should be the id::

     >>> tfile = tempfile(secret_file_name)
     >>> form = {'attachmentFile': tfile}
     >>> request.form = form
     >>> view.create_attachment()
     {...'oc-wiki-attachments'...}
     >>> newatt = view.context._getOb('secret.txt')
     >>> newatt
     <FileAttachment at /plone/projects/p1/project-home/secret.txt>
     >>> newatt.Title()
     'secret.txt'

Test update attachment... first check error case::

     >>> request.form = {}
     >>> view.update_attachment()
     {}

Try again with real values, should work great now::

     >>> view.update_attachment(['secret.txt'], [{'title': "Alcibiades"}])
     {'secret.txt_list-item':...Alcibiades...}

Try listing the attachments
     >>> brains = view.fileAttachments()
     >>> [b.getId for b in brains]
     ['secret.txt']
     >>> brain = brains[0]
     >>> brain.Title
     'Alcibiades'

IMAGE MANAGER BACKEND
=====================

     >>> view = page.restrictedTraverse('@@backend')
     >>> view
     <...SimpleViewClass from ...wiki/backend.pt object at ...>

     >>> view = page.restrictedTraverse('@@backend-images')
     >>> view
     <...SimpleViewClass from ...wiki/backend-images.pt object at ...>

Upload an attachment

     >>> request = self.portal.REQUEST
     >>> nui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
     >>> filename = os.path.join(nui_dir, 'wiki', 'logo.gif')
     >>> open(filename).read()
     'GIF...
     >>> imgfile = tempfile(filename)
     >>> form = {'attachmentFile': imgfile}
     >>> request.form = form

and check that it appears in the list of files
(should it be unicode output?)
     >>> view.create_attachment_manager()
     '<...203x50...

(the magic number is the size of xinha_logo.gif)    

and delete it
     >>> request.form = {'task|logo.gif|delete-image' : 'Delete'}
     >>> import re
     >>> empty_body = re.compile('<body>\s*</body>')
     >>> empty_body.search(view())
     <_sre.SRE_Match object at ...>
     

boy, those 



VERSION COMPARE
===============

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
     >>> view.portal_status_message
     [u'Please choose the two versions you would like to compare.']

Reset the request
     >>> request = view.request.form = {}

Try it with just one argument
     >>> request['version_id'] = '0'
     >>> response = view()
     Traceback (most recent call last):
     ...
     Redirect: http://nohost/plone/projects/p1/project-home/history
     >>> view.portal_status_message
     [u'Please choose the two versions you would like to compare.']

Try with 2 arguments, but the versions don't exist
     >>> request['version_id'] = ['0', '1']
     >>> response = view()
     Traceback (most recent call last):
     ...
     Redirect: http://nohost/plone/projects/p1/project-home/history
     >>> view.portal_status_message
     [u'Please choose a valid version.']

Try with more than 2 versions
     >>> request['version_id'] = ['0', '1', '2']
     >>> response = view()
     Traceback (most recent call last):
     ...
     Redirect: http://nohost/plone/projects/p1/project-home/history
     >>> view.portal_status_message
     [u'Please choose only two versions to compare.']

Now edit 2 pages, so we can try a valid compare later
     >>> request['version_id'] = ['0', '1']
     >>> repo = view.get_tool('portal_repository')
     >>> page.processForm(values=dict(text='some new text'))
     >>> repo.save(page, comment='new comment')
     >>> page.processForm(values=dict(text='some even newer text'))
     >>> repo.save(page, comment='newest comment')

Now we should get a valid response
     >>> view.loggedinmember.getId = lambda *a:'whatever'
     >>> response = view()

Test that we can create a page via wicked
     >>> view = page.restrictedTraverse('@@add-page')
     >>> view
     <Products.Five.metaclass.NuiPageAdd object at ...>

     >>> request = self.portal.REQUEST 
     >>> request.form = {'Title' : 'newpage', 'section' : 'text'}
     >>> view()
     'http://...projects/p1/newpage/edit...'

Login as different users, each time checking the last modified author
     >>> self.logout()
     >>> self.login('m1')
     >>> view = page.restrictedTraverse('@@edit')
     >>> view
     <Products.Five.metaclass.WikiEdit object at ...>

Now start changing the page
     >>> request = view.request.form
     >>> request['text'] = u'<p>foo<br>\n\u2255baz</p>'.encode('utf-8')
     >>> request['title'] = 'bar'
     >>> view.handle_save()

Verify the last modified author and text changes took place
     >>> proj = self.portal.projects.p1
     >>> from opencore.interfaces.catalog import ILastModifiedAuthorId
     >>> ILastModifiedAuthorId(page)
     'm1'
     >>> ILastModifiedAuthorId(proj)
     'm1'

     >>> page.text.raw
     u'<p>foo<br>\n&#8789;baz</p>'

     >>> self.logout()
     >>> self.login('m3')
     >>> view = page.restrictedTraverse('@@edit')
     >>> request = view.request.form
     >>> request['text'] = 'bar'
     >>> view.handle_save()
     >>> ILastModifiedAuthorId(page)
     'm3'
     >>> ILastModifiedAuthorId(proj)
     'm3'

Check that when logging back in as m1, m3 is still the last modified author
     >>> ILastModifiedAuthorId(page)
     'm3'
     >>> ILastModifiedAuthorId(proj)
     'm3'

Experimental marking should no longer control which template is used
     >>> from opencore.interfaces import IAmExperimental
     >>> IAmExperimental.providedBy(proj)
     False

Check for xinha
     >>> html = view.template()
     >>> 'kupu' in html
     False
     >>> 'xinha' in html
     True

News Edit View
==============

Create a new news item
     >>> self.loginAsPortalOwner()
     >>> from opencore.nui.main.search import NewsView
     >>> add_news_view = NewsView(self.portal.news,
     ...                          self.portal.REQUEST)
     >>> add_news_view.add_new_news_item()
     >>> news_items = self.portal.news.objectIds()
     >>> assert len(news_items) == 1
     >>> ni = getattr(self.portal.news, news_items[0])

Now that we have a new news item, let's simulate an edit
     >>> from opencore.nui.wiki.view import WikiNewsEditView
     >>> view = WikiNewsEditView(ni, self.portal.REQUEST)
     >>> request = view.request.form
     >>> request.update(dict(
     ...   title='news title',
     ...   description='news description',
     ...   ))
     >>> view.handle_save()
     >>> view.request.response.getHeader('location')
     'http://nohost/plone/news/...'
     >>> ni.Title()
     'news title'
     >>> ni.Description()
     'news description'

And when asking for news items, the description brain is set
     >>> [b.Description for b in add_news_view.news_items()]
     ['news description']
