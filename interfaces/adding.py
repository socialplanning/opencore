"""
$Id: __init__.py,v 1.2 2005/02/26 17:56:10 sidnei Exp $
"""

from zope.interface import Interface

class IAddProject(Interface):
    """Marker interface that indicates OpenProjects can be added.
    """

class IAmAPeopleFolder(Interface):
    """Marker interface that indicates that this folder contains people"""

class IAmANewsFolder(Interface):
    """Marker interface that indicates that this is the OpenPlans news folder"""
