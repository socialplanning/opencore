from Products.CMFCore.utils import getToolByName

from Products.OpenPlans.interfaces import IReadWorkflowPolicySupport
from Products.OpenPlans.workflows import PLACEFUL_POLICIES

def migrate_project_workflow(self):
    out = []
    wftool = getToolByName(self, 'portal_workflow')
    cat = getToolByName(self, 'portal_catalog')
    proj_brains = cat(Type='OpenProject')
    for brain in proj_brains:
        proj = brain.getObject()
        policy_reader = IReadWorkflowPolicySupport(proj)
        policy = policy_reader.getCurrentPolicyId()
        transition = PLACEFUL_POLICIES[policy]['proj_trans']
        for available_trans in wftool.getTransitionsFor(proj):
            if transition == available_trans['id']:
                wftool.doActionFor(proj, transition)
                out.append('Changed status for %s using transition: %s' % \
                           (proj.getId(), transition))
                break
    return "\n".join(out)
