"""
OpenPlans
~~~~~~~~~~

Integration product for the Open Planning Project platform
to be hosted at http://www.openplans.org/

"""
__authors__ = 'Rob Miller <robm@openplans.org>'
__docformat__ = 'restructuredtext'

import os.path
from App.Common import package_home
from opencore.configuration import DEFAULT_ROLES, DEFAULT_ACTIVE_MSHIP_STATES
from opencore.configuration import PROJECTNAME, COOKIE_DOMAIN
from opencore.configuration import PROHIBITED_MEMBER_PREFIXES

GLOBALS                = globals()

PKG_HOME               = package_home(GLOBALS)
SKINS_DIR              = 'skins'

NOT_ADDABLE_TYPES = ['Smartlink', 'IronicWiki', 'TeamSpace']

NAVTREE_TYPES = ['Collector', 'HelpCenterErrorReferencefolder',
                 'HelpCenterFAQFolder', 'Folder', 'HelpCenter',
                 'HelpCenterHowToFolder', 'Large Plone Folder',
                 'HelpCenterLinkFolder', 'OpenProject',
                 'HelpCenterReferenceManualFolder',
                 'HelpCenterReferenceManualSection',
                 'Topic', 'WeblogTopic', 'HelpCenterTutorialFolder',
                 'HelpCenterInstructionalVideoFolder',
                 ]

SITE_INDEX_TEMPLATE = 'site_index_html'

try:
    # When Reference are in CMFCore
    from Products.CMFCore.reference_config import *
    from Products.CMFCore.ReferenceCatalog import Reference
    from Products.CMFCore.Referenceable import Referenceable
except ImportError:
    # And while they still live in Archetypes
    from Products.Archetypes.ReferenceEngine import Reference
    from Products.Archetypes.Referenceable import Referenceable
    from Products.Archetypes.config import REFERENCE_CATALOG as REFERENCE_MANAGER
    from Products.Archetypes.config import UID_CATALOG as UID_MANAGER
