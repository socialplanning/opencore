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


class WorkflowPolicyWriteAdapter(WorkflowPolicyReadAdapter):
    """ An adapter for setting the local workflow policy """

    implements(IWriteWorkflowPolicySupport)

    def _update_team_state(self, policy_in):
        """ update the team state as well on project policy changes
            (this ensures that mship objects get right permission) """
        new_policy = policy_in == 'closed_policy' and \
                     'mship_closed_policy' or \
                     'mship_open_policy'
        project = self.context
        teams_tool = getToolByName(project, 'portal_teams')
        proj_id = project.getId()
        
        team_ob = teams_tool._getOb(proj_id)

        # check if a transition doesn't have to be made
        old_policy = self.getCurrentPolicyId(team_ob)
        if old_policy == new_policy: return

        pwf = getToolByName(team_ob, 'portal_placeful_workflow')
        config = pwf.getWorkflowPolicyConfig(team_ob)
        if config is None:
            addP = team_ob.manage_addProduct['CMFPlacefulWorkflow']
            addP.manage_addWorkflowPolicyConfig()
            config = pwf.getWorkflowPolicyConfig(team_ob)

        # XXX only update teams
        # for some reason, an OpenProject gets in here sometimes
        # we need to call the manage_makeChanges method for the placeful
        # workflow team tests, but this fails for the openplans project tests
        config.manage_makeChanges(new_policy, new_policy)

        self._migrate_histories_on(team_ob, old_policy, new_policy)

    def _migrate_histories_on(self, team, old_wfid, new_wfid):
        """ since the workflow changed, move the entire history
            from the old workflow to the new one """

        wft = getToolByName(self.context, 'portal_workflow')
        if old_wfid == 'mship_open_policy':
            old_id = 'openplans_team_membership_workflow'
            new_id = 'closed_openplans_team_membership_workflow'
        else:
            old_id = 'closed_openplans_team_membership_workflow'
            new_id = 'openplans_team_membership_workflow'
        mship_ids = team.objectIds()
        for mship_id in mship_ids:
            # don't copy over the wf policy config
            if mship_id == '.wf_policy_config': continue
            mship = team._getOb(mship_id)
            # bad touch the workflow history, because their is no set api
            wfh = mship.workflow_history
            if old_id in wfh:
                wfh[new_id] = wfh[old_id]

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
            # we need to also update the team state
            # XXX we have an ugly hack here to make the tests
            # pass however
            update_role_mappings = True

        if context.getTeams():
            self._update_team_state(policy_in)
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
            if teams:
                count += wftool._recursiveUpdateRoleMappings(team, wfs)
            return count
