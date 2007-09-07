"""
$Id: __init__.py,v 1.2 2005/02/26 17:56:10 sidnei Exp $
"""

from zope.interface import Interface

class IProject(Interface):
    """Dummy interface for an abstract project class
    """

    def projectMemberIds(admin_only=False):
        """List ids for all the members of this project, optionally limited to
           only admins.
        """

    def projectMembers(admin_only=False):
        """List all the members of this project, optionally limited to
           only admins.
        """