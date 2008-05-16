"""
$Id: __init__.py,v 1.2 2005/02/26 17:56:10 sidnei Exp $
"""

from opencore.interfaces.workflow import IReadWorkflowPolicySupport
from opencore.interfaces.workflow import IWriteWorkflowPolicySupport
from warnings import warn

warn('%s is a deprecated import path. Please use opencore.interfaces.workflow' %__name__)
