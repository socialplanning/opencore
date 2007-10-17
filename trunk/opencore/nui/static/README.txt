================
 static content
================

This folder is for static content to be pulled in to views.

    >>> from opencore.nui.static import render_static
    >>> render_static('test.txt')
    'This is a test message.\n'

If we try to render a file that does not exist, we should get an exception

    >>> render_static('thisfiledoesnotexist.txt')
    Traceback (most recent call last):
    ...
    IOError: [Errno 2] No such file or directory: '...'
