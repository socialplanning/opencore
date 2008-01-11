from Acquisition import aq_get, aq_inner, aq_base
from Products.CMFCore.utils import getToolByName
from Products.CMFPlacefulWorkflow.PlacefulWorkflowTool import WorkflowPolicyConfig_id
from opencore.interfaces.workflow import IWriteWorkflowPolicySupport
from opencore.interfaces.workflow import IReadWorkflowPolicySupport
from Products.OpenPlans.workflows import PLACEFUL_POLICIES
from Products.OpenPlans.workflows import MEMBERSHIP_PLACEFUL_POLICIES

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


class WFPolicyReadAdapter(object):
    """ An adapter for getting information about the local workflow
    policy """

    implements(IReadWorkflowPolicySupport)

    def __init__(self, context):
        self.context = context

    def getCurrentPolicyId(self, ob=None):
        if ob is None:
            ob = self.context
        wf_id = ''
        pwf = getToolByName(ob, 'portal_placeful_workflow')
        config = pwf.getWorkflowPolicyConfig(ob)
        if config is not None:
            wf_id = config.getPolicyInId()
        else:
            # Get the default from the container via acquisition
            config = aq_get(aq_inner(ob), WorkflowPolicyConfig_id, None)
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


class WFPolicyWriteAdapter(WFPolicyReadAdapter):
    """ An abstract base class for and adapter which sets the local
    workflow policy """

    implements(IWriteWorkflowPolicySupport)

    def _getPolicyData(self):
        return self.policy_data

    @property
    def policy_data(self):
        raise NotImplementedError

    def _perform_role_mappings_update(self):
        wft = getToolByName(self.context, 'portal_workflow')
        wfs = {}
        for wf_id in wft.listWorkflows():
            wf = wft.getWorkflowById(wf_id)
            wfs[wf_id] = wf
        # bad touching to avoid waking up the entire portal
        count = wft._recursiveUpdateRoleMappings(self.context, wfs)
        return count

    def setPolicy(self, policy_in, skip_update_role_mappings=False):
        context = self.context
        pwf = getToolByName(context, 'portal_placeful_workflow')
        config = pwf.getWorkflowPolicyConfig(context)
        if config is None:
            addP = context.manage_addProduct['CMFPlacefulWorkflow']
            addP.manage_addWorkflowPolicyConfig()
            config = pwf.getWorkflowPolicyConfig(context)
        
        wftool = getToolByName(context, 'portal_workflow')
        update_role_mappings = False
        if self.getCurrentPolicyId() != policy_in:
            config.manage_makeChanges(policy_in, policy_in)
            update_role_mappings = True

        # we may have to change state of the context object
        policy_data = self._getPolicyData()
        context_trans = policy_data[policy_in].get('context_trans')
        for available_trans in wftool.getTransitionsFor(context):
            if context_trans == available_trans['id']:
                wftool.doActionFor(context, context_trans)
                update_role_mappings = True
                break

        if skip_update_role_mappings:
            return update_role_mappings
        elif update_role_mappings:
            count = self._perform_role_mappings_update()
        else:
            count = 0

        return count


class ProjectWFPolicyWriteAdapter(WFPolicyWriteAdapter):
    """
    WF policy write adapter for IProject objects.  base class does
    most of the work, this class adds the following customizations:

    o retrieves the right policy config data structure

    o triggers the team object to change its workflow policy
    """
    policy_data = PLACEFUL_POLICIES 

    def setPolicy(self, policy_in):
        count = WFPolicyWriteAdapter.setPolicy(self, policy_in)

        teams = self.context.getTeams()
        if teams:
            policy_data = self._getPolicyData()
            team_policy_in = policy_data[policy_in]['team_policy']

            team = teams[0]
            team_policy_writer = IWriteWorkflowPolicySupport(team)
            count += team_policy_writer.setPolicy(team_policy_in)

        return count


class TeamWFPolicyWriteAdapter(WFPolicyWriteAdapter):
    """
    WF policy write adapter for IOpenTeam objects.  base class does
    most of the work, this class adds the following customizations:

    o retrieves the right policy config data structure

    o copies the w/f history for each contained membership object
    """
    policy_data = MEMBERSHIP_PLACEFUL_POLICIES 

    def setPolicy(self, policy_in):
        """
        Set the w/f policy on the team object.  Also copies the w/f
        history for each contained membership, using a bit of bad
        touch.
        """
        team = self.context
        wft = getToolByName(team, 'portal_workflow')
        mship = team.objectValues(spec='OpenMembership')[0]
        old_wf_id = wft.getChainFor(mship)[0]

        parent_setPolicy = WFPolicyWriteAdapter.setPolicy
        update_role_mappings = parent_setPolicy(self, policy_in,
                                                skip_update_role_mappings=True)

        new_wf_id = wft.getChainFor(mship)[0]
        if old_wf_id != new_wf_id:
            update_role_mappings = True
            # workflow has changed
            mships = team.getMemberships()
            for mship in mships:
                # bad touch the workflow history to copy the history
                # for one workflow to the other; this preserves the
                # state information for the membership objects
                wfh = mship.workflow_history
                if old_wf_id in wfh:
                    wfh[new_wf_id] = wfh[old_wf_id]

        count = 0
        if update_role_mappings:
            count = self._perform_role_mappings_update()

        return count
