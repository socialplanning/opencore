# BBB
from opencore.interfaces import IEditProject
from opencore.interfaces import IOpenTeam 
from opencore.interfaces import IProject
from opencore.interfaces.membership import IOpenMembership
from opencore.interfaces.workflow import IReadWorkflowPolicySupport
from opencore.interfaces.workflow import IWriteWorkflowPolicySupport

from warnings import warn
warn("please import interfaces from opencore.interfaces, rather than 'Products.OpenPlans.interfaces'")
