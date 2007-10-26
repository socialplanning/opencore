=========
 utility
=========

This package is dedicated to the most general of utilities.

    >>> from opencore.utility.interfaces import IHTTPClient
    >>> getUtility(IHTTPClient)
    <httplib2.Http ... at ...>

Do an override::

    >>> from zope.component import provideUtility
    >>> mockhttp = mock_utility('httplib2.Http', IHTTPClient)
    >>> provideUtility(component=mockhttp, provides=IHTTPClient)
    >>> getUtility(IHTTPClient)
    <Mock ... httplib2.Http>
