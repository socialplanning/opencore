from Acquisition import aq_get, aq_inner, aq_base
from Products.CMFCore.utils import getToolByName
from Products.CMFPlacefulWorkflow.PlacefulWorkflowTool import WorkflowPolicyConfig_id
from Products.OpenPlans.interfaces import IWriteWorkflowPolicySupport
from Products.OpenPlans.interfaces import IReadWorkflowPolicySupport
from Products.OpenPlans.workflows import PLACEFUL_POLICIES

from zope.interface import implements
from zope.component import getMultiAdapter

def saveWFPolicy(obj, event):
    """ IObjectModified event subscriber that changes the wf policy """
    req = obj.REQUEST
    new_policy = req.form.get('workflow_policy', '')
    if new_policy:
        view = getMultiAdapter((obj, req), name=u'policy_writer')
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
        
        wftool = getToolByName(self.context, 'portal_workflow')
        update_role_mappings = False
        if self.getCurrentPolicyId() != policy_in:
            config.manage_makeChanges(policy_in, policy_in)
            update_role_mappings = True

        # we may have to change state of project/team objects
        proj_trans = PLACEFUL_POLICIES[policy_in]['proj_trans']
        for available_trans in wftool.getTransitionsFor(self.context):
            if proj_trans == available_trans['id']:
                wftool.doActionFor(self.context, proj_trans)
                update_role_mappings = True
                break
        teams = self.context.getTeams()
        if teams:
            team = teams[0]
            for available_trans in wftool.getTransitionsFor(team):
                if proj_trans == available_trans['id']:
                    wftool.doActionFor(team, proj_trans)
                    update_role_mappings = True
                    break

        if update_role_mappings:
            wfs = {}
            for wf_id in wftool.listWorkflows():
                wf = wftool.getWorkflowById(wf_id)
                wfs[wf_id] = wf
            # XXX: Bad Touching to avoid waking up the entire portal
            count = wftool._recursiveUpdateRoleMappings(self.context, wfs)
            return count
