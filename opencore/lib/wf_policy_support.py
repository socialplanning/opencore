from Acquisition import aq_get, aq_inner, aq_base
from Products.CMFCore.utils import getToolByName
from Products.CMFPlacefulWorkflow.PlacefulWorkflowTool import WorkflowPolicyConfig_id
from Products.OpenPlans.workflows import PLACEFUL_POLICIES
from opencore.interfaces import IReadWorkflowPolicySupport
from opencore.interfaces import IWriteWorkflowPolicySupport
from zope.component import queryView
from zope.interface import implements

def saveWFPolicy(obj, event):
    """ IObjectModified event subscriber that changes the wf policy """
    req = obj.REQUEST
    new_policy = req.get('workflow_policy', '')
    if new_policy:
        view = queryView(obj, u'policy_writer', req)
        if view is not None:
            view.setPolicy(new_policy)


class WorkflowPolicyReadAdapter(object):
    """ An adapter for getting information about the local workflow policy """

    implements(IReadWorkflowPolicySupport)

    def __init__(self, context):
        self.context = context

    def getCurrentPolicyId(self):
        wf_id = ''
        pwf = getToolByName(self.context, 'portal_placeful_workflow')
        config = pwf.getWorkflowPolicyConfig(self.context)
        if config is not None:
            wf_id = config.getPolicyInId()
        else:
            # Get the default from the container via acquisition
            config = aq_get(aq_inner(self.context), WorkflowPolicyConfig_id, None)
            if config is not None:
                wf_id = config.getPolicyBelowId()
        return wf_id

    def getAvailablePolicies(self):
        # We acquire a default config if available as opposed to the tool method
        pwf = getToolByName(self.context, 'portal_placeful_workflow')
        policies = pwf.getWorkflowPolicies()
        list_policies = [{'id': p.getId(),
                          'title': p.getTitle(),
                          'description': p.getDescription()}
                         for p in policies]
        return list_policies


class WorkflowPolicyWriteAdapter(WorkflowPolicyReadAdapter):
    """ An adapter for setting the local workflow policy """

    implements(IWriteWorkflowPolicySupport)

    def setPolicy(self, policy_in):
        context = self.context
        pwf = getToolByName(context, 'portal_placeful_workflow')
        config = pwf.getWorkflowPolicyConfig(context)
        if config is None:
            addP = self.context.manage_addProduct['CMFPlacefulWorkflow']
            addP.manage_addWorkflowPolicyConfig()
            config = pwf.getWorkflowPolicyConfig(context)
        if self.getCurrentPolicyId() != policy_in:
            config.manage_makeChanges(policy_in, policy_in)

            pwf = getToolByName(self.context, 'portal_workflow')
            wfs = {}
            for id in pwf.objectIds():
                wf = pwf.getWorkflowById(id)
                if hasattr(aq_base(wf), 'updateRoleMappingsFor'):
                    wfs[id] = wf

            # possibly change wf state of the project itself
            proj_trans = PLACEFUL_POLICIES[policy_in]['proj_trans']
            for available_trans in pwf.getTransitionsFor(self.context):
                if proj_trans == available_trans['id']:
                    pwf.doActionFor(self.context, proj_trans)
                    break

            # XXX: Bad Touching to avoid waking up the entire portal
            count = pwf._recursiveUpdateRoleMappings(self.context, wfs)
            return count
