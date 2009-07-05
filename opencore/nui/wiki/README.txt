-*- mode: doctest ;-*-

=========
 wiki ui
=========


Edit tab
========

Make sure notallowed css class is applied to edit tab since we don't
have permissions to edit::

    >>> page = getattr(self.portal.projects.p1, page_id)
    >>> request = self.portal.REQUEST
    >>> from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
    >>> from opencore.nui.wiki import view as viewpkg
    >>> import os.path
    >>> prefix = os.path.dirname(__file__)
    >>> pageview = viewpkg.WikiView(page, request)
    >>> pageview = pageview.__of__(page)
    >>> pageview.__call__ = ViewPageTemplateFile('wiki-view.pt', _prefix=prefix)
    >>> 'oc-notallowed' in pageview()
    True

Log in, then make sure notallowed css class is _not_ applied to edit
tab since we do have permissions to edit::

    >>> self.loginAsPortalOwner()
    >>> 'oc-notallowed' in pageview()
    False


Linking
=======

Test whether wicked linking works correctly:

     >>> from opencore.nui.wiki.view import xinha_to_wicked
     >>> xinha_to_wicked('<html>((foo))</html>')
     '<html>((foo))</html>'

Note that this is a string.  If I try this with an HTML escaped
character it becomes unicode:     

     >>> xinha_to_wicked('<html>((&#38;))</html>')
     u'<html>((&))</html>'

Now try a link with an ASCII character greater than 127:

    >>> xinha_to_wicked('<html>((hello \xc2))</html>')
    '<html>((hello \xc2))</html>'

Now try a link with an HTML escape sequence -AND- and ASCII character
greater than 127:

    >>> xinha_to_wicked(u'<html>((&#38; hello \xc3\x82))</html>')
    u'<html>((& hello \xc3\x82))</html>'

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

     >>> view = viewpkg.WikiEdit(page, request)
     >>> view = view.__of__(page)
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

Deleting the same attachment should not produce an error. This will be the case
if two requests come in to delete the same attachment::

    >>> view.delete_attachment(['secret.txt'])
    {}

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

     >>> view = viewpkg.ImageManager(page, request)
     >>> view = view.__of__(page)

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
(should it be unicode output?) -- the magic number
we're searching for here is the size of xinha_logo.gif
     >>> print view.create_attachment_manager()
     <...203x50...

and delete it
     >>> request.form = {'task|logo.gif|delete-image' : 'Delete'}
     >>> import re
     >>> empty_body = re.compile('<body>\s*</body>')
     >>> empty_body.search(view())
     <_sre.SRE_Match object at ...>
     

boy, those 


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
     ...   text='news'
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
