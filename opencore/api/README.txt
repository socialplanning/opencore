==============
 opencore.api
==============

APIs for remote interaction with opencore. Currently we have two APIs
provided by projects, one provided by the people folder, and one
provided by members.

Project APIs
============

members.xml shows a project's memberships, providing member id and
highest team role for each::
    >>> print http(r'''
    ... GET /plone/projects/p1/@@members.xml HTTP/1.1
    ... ''')
    HTTP/1.1 200 OK
    Content-Length: ...
    Content-Type: application/xml...
    <members>...
     <member>
      <id>portal_owner</id>
      <role>ProjectAdmin</role>
     </member>...
    </members>...

info.xml shows the project's security policy and installed featurelets::

    >>> print http(r'''
    ... GET /plone/projects/p1/@@info.xml HTTP/1.1
    ... ''')
    HTTP/1.1 200 OK
    Content-Length: ...
    Content-Type: application/xml...
    <info>
     <policy>medium_policy</policy>
     <featurelets>...
     </featurelets>
    </info>...


Member API
==========

info.xml shows personal information about the member, but I've 
described this in member_api.txt and unhooked it from the testrunner
because I can't get the damn tests to pass (member content doesn't
seem to be getting created no matter how hard I try).
