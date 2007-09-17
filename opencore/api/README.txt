==============
 opencore.api
==============

APIs for remote interaction with opencore.

Currently we have 2 APIs provided by project.

Members show a project's members, providing id and highest team role
for each::
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

Project info shows the project's security policy::
    >>> print http(r'''
    ... GET /plone/projects/p1/@@info.xml HTTP/1.1
    ... ''')
    HTTP/1.1 200 OK
    Content-Length: ...
    Content-Type: text/html; charset=utf-8...
    <info>...
    <policy>medium_policy</policy>
    </info>...


