#
# Generated by dumpDCWorkflow.py written by Sebastien Bigaret
# Original workflow id/title: open_policy_workflow/Open Security Policy Workflow
# Date: 2007/08/13 19:27:53.591 GMT-4
#
# WARNING: this dumps does NOT contain any scripts you might have added to
# the workflow, IT IS YOUR RESPONSABILITY TO MAKE BACKUPS FOR THESE SCRIPTS.
#
# No script detected in this workflow
#
"""
Programmatically create a workflow type.
"""
__version__ = "$Id: dumpDCWorkflow.py 25723 2006-07-04 08:41:22Z b_mathieu $"

from Products.CMFCore.WorkflowTool import addWorkflowFactory
from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.PythonScripts.PythonScript import PythonScript
from Products.ExternalMethod.ExternalMethod import ExternalMethod

def setup_open_policy_workflow(wf):
    """Setup the workflow
    """
    wf.setProperties(title='Open Security Policy Workflow')

    for s in ('team_visible', 'team_visible_locked', 'visible', 'visible_locked'):
        wf.states.addState(s)
    for t in ('lockAsTeamVisible',
              'lockAsVisible',
              'makeVisible',
              'team',
              'unlockAsTeamVisible',
              'unlockAsVisible'):
        wf.transitions.addTransition(t)
    for v in ('action', 'actor', 'comments', 'review_history', 'time'):
        wf.variables.addVariable(v)
    for l in ():
        wf.worklists.addWorklist(l)
    for p in ('Access contents information',
              'Modify portal content',
              'View',
              'Delete objects',
              'CMFEditions: Access previous versions',
              'CMFEditions: Save new version',
              'CMFEditions: Apply version control',
              'CMFEditions: Revert to previous versions',
              'Add RichDocument',
              'OpenPlans: Add OpenPage'):
        wf.addManagedPermission(p)

    # Initial State
    wf.states.setInitialState('visible')

    # State Initialization
    sdef = wf.states['team_visible']
    sdef.setProperties(title='Mgmt Only',
                       description='',
                       transitions=('lockAsTeamVisible', 'makeVisible'))
    sdef.setPermission('Access contents information', 0,
                       ['Manager', 'Owner', 'ProjectAdmin', 'ProjectContentMgr'])
    sdef.setPermission('Modify portal content', 0,
                       ['Manager', 'ProjectAdmin', 'ProjectContentMgr'])
    sdef.setPermission('View', 0,
                       ['Manager', 'Owner', 'ProjectAdmin', 'ProjectContentMgr'])
    sdef.setPermission('Delete objects', 0,
                       ['Manager', 'ProjectAdmin', 'ProjectContentMgr'])
    sdef.setPermission('CMFEditions: Access previous versions', 0,
                       ['Manager', 'Owner', 'ProjectAdmin', 'ProjectContentMgr'])
    sdef.setPermission('CMFEditions: Save new version', 0,
                       ['Manager', 'ProjectAdmin', 'ProjectContentMgr'])
    sdef.setPermission('CMFEditions: Apply version control', 0,
                       ['Manager', 'ProjectAdmin', 'ProjectContentMgr'])
    sdef.setPermission('CMFEditions: Revert to previous versions', 0,
                       ['Manager', 'ProjectAdmin', 'ProjectContentMgr'])
    sdef.setPermission('Add RichDocument', 1,
                       [])
    sdef.setPermission('OpenPlans: Add OpenPage', 1,
                       [])

    sdef = wf.states['team_visible_locked']
    sdef.setProperties(title='Mgmt Only - Locked',
                       description='',
                       transitions=('unlockAsTeamVisible',))
    sdef.setPermission('Access contents information', 0,
                       ['Manager', 'Owner', 'ProjectAdmin', 'ProjectContentMgr'])
    sdef.setPermission('Modify portal content', 0,
                       ['Manager', 'ProjectAdmin'])
    sdef.setPermission('View', 0,
                       ['Manager', 'Owner', 'ProjectAdmin', 'ProjectContentMgr'])
    sdef.setPermission('Delete objects', 0,
                       ['Manager', 'ProjectAdmin'])
    sdef.setPermission('CMFEditions: Access previous versions', 0,
                       ['Manager', 'Owner', 'ProjectAdmin', 'ProjectContentMgr'])
    sdef.setPermission('CMFEditions: Save new version', 0,
                       ['Manager', 'ProjectAdmin'])
    sdef.setPermission('CMFEditions: Apply version control', 0,
                       ['Manager', 'ProjectAdmin'])
    sdef.setPermission('CMFEditions: Revert to previous versions', 0,
                       ['Manager', 'ProjectAdmin'])
    sdef.setPermission('Add RichDocument', 1,
                       [])
    sdef.setPermission('OpenPlans: Add OpenPage', 1,
                       [])

    sdef = wf.states['visible']
    sdef.setProperties(title='Public',
                       description='',
                       transitions=('lockAsVisible', 'team'))
    sdef.setPermission('Access contents information', 0,
                       ['Anonymous',
                       'Authenticated',
                       'Manager',
                       'Member',
                       'Owner',
                       'ProjectAdmin',
                       'ProjectMember',
                       'Reviewer'])
    sdef.setPermission('Modify portal content', 0,
                       ['Manager', 'Member', 'Owner', 'ProjectAdmin', 'ProjectMember', 'Reviewer'])
    sdef.setPermission('View', 0,
                       ['Anonymous',
                       'Authenticated',
                       'Manager',
                       'Member',
                       'Owner',
                       'ProjectAdmin',
                       'ProjectMember',
                       'Reviewer'])
    sdef.setPermission('Delete objects', 0,
                       ['Manager', 'ProjectAdmin', 'ProjectMember', 'Reviewer'])
    sdef.setPermission('CMFEditions: Access previous versions', 0,
                       ['Anonymous',
                       'Authenticated',
                       'Manager',
                       'Member',
                       'Owner',
                       'ProjectAdmin',
                       'ProjectMember',
                       'Reviewer'])
    sdef.setPermission('CMFEditions: Save new version', 0,
                       ['Manager', 'Member', 'Owner', 'ProjectAdmin', 'ProjectMember', 'Reviewer'])
    sdef.setPermission('CMFEditions: Apply version control', 0,
                       ['Manager', 'Member', 'Owner', 'ProjectAdmin', 'ProjectMember', 'Reviewer'])
    sdef.setPermission('CMFEditions: Revert to previous versions', 0,
                       ['Manager', 'Member', 'Owner', 'ProjectAdmin', 'ProjectMember', 'Reviewer'])
    sdef.setPermission('Add RichDocument', 0,
                       ['Manager', 'Member', 'Owner', 'ProjectAdmin', 'ProjectMember', 'Reviewer'])
    sdef.setPermission('OpenPlans: Add OpenPage', 0,
                       ['Manager', 'Member', 'Owner', 'ProjectAdmin', 'ProjectMember', 'Reviewer'])

    sdef = wf.states['visible_locked']
    sdef.setProperties(title='Visible - Locked',
                       description='',
                       transitions=('unlockAsVisible',))
    sdef.setPermission('Access contents information', 0,
                       ['Anonymous',
                       'Authenticated',
                       'Manager',
                       'Member',
                       'Owner',
                       'ProjectAdmin',
                       'ProjectContentMgr',
                       'ProjectMember',
                       'Reviewer'])
    sdef.setPermission('Modify portal content', 0,
                       ['Manager', 'ProjectAdmin'])
    sdef.setPermission('View', 0,
                       ['Anonymous',
                       'Authenticated',
                       'Manager',
                       'Member',
                       'Owner',
                       'ProjectAdmin',
                       'ProjectContentMgr',
                       'ProjectMember',
                       'Reviewer'])
    sdef.setPermission('Delete objects', 0,
                       ['Manager', 'ProjectAdmin'])
    sdef.setPermission('CMFEditions: Access previous versions', 0,
                       ['Manager', 'Owner', 'ProjectAdmin', 'ProjectContentMgr'])
    sdef.setPermission('CMFEditions: Save new version', 0,
                       ['Manager', 'ProjectAdmin'])
    sdef.setPermission('CMFEditions: Apply version control', 0,
                       ['Manager', 'ProjectAdmin'])
    sdef.setPermission('CMFEditions: Revert to previous versions', 0,
                       ['Manager', 'ProjectAdmin'])
    sdef.setPermission('Add RichDocument', 1,
                       [])
    sdef.setPermission('OpenPlans: Add OpenPage', 1,
                       [])

    # Transition Initialization
    tdef = wf.transitions['lockAsTeamVisible']
    tdef.setProperties(title='Lock',
                       description='',
                       new_state_id='team_visible_locked',
                       trigger_type=1,
                       script_name='',
                       after_script_name='',
                       actbox_name='Lock',
                       actbox_url='',
                       actbox_category='workflow',
                       props={'guard_roles': 'ProjectAdmin'},
                       )

    tdef = wf.transitions['lockAsVisible']
    tdef.setProperties(title='Lock',
                       description='',
                       new_state_id='visible_locked',
                       trigger_type=1,
                       script_name='',
                       after_script_name='',
                       actbox_name='Lock',
                       actbox_url='',
                       actbox_category='workflow',
                       props={'guard_roles': 'ProjectAdmin'},
                       )

    tdef = wf.transitions['makeVisible']
    tdef.setProperties(title='Make Public',
                       description='',
                       new_state_id='visible',
                       trigger_type=1,
                       script_name='',
                       after_script_name='',
                       actbox_name='Make Public',
                       actbox_url='',
                       actbox_category='workflow',
                       props={'guard_permissions': 'OpenPlans: Make content visible'},
                       )

    tdef = wf.transitions['team']
    tdef.setProperties(title='Make Mgmt Only',
                       description='',
                       new_state_id='team_visible',
                       trigger_type=1,
                       script_name='',
                       after_script_name='',
                       actbox_name='Make Mgmt Only',
                       actbox_url='%(content_url)s/what_is_this_for',
                       actbox_category='workflow',
                       props={'guard_permissions': 'Modify portal content'},
                       )

    tdef = wf.transitions['unlockAsTeamVisible']
    tdef.setProperties(title='Unlock',
                       description='',
                       new_state_id='team_visible',
                       trigger_type=1,
                       script_name='',
                       after_script_name='',
                       actbox_name='Unlock',
                       actbox_url='',
                       actbox_category='workflow',
                       props={'guard_roles': 'ProjectAdmin'},
                       )

    tdef = wf.transitions['unlockAsVisible']
    tdef.setProperties(title='Unlock',
                       description='',
                       new_state_id='visible',
                       trigger_type=1,
                       script_name='',
                       after_script_name='',
                       actbox_name='Unlock',
                       actbox_url='',
                       actbox_category='workflow',
                       props={'guard_roles': 'ProjectAdmin'},
                       )

    # State Variable
    wf.variables.setStateVar('review_state')

    # Variable Initialization
    vdef = wf.variables['action']
    vdef.setProperties(description='The last transition',
                       default_value='',
                       default_expr='transition/getId|nothing',
                       for_catalog=0,
                       for_status=1,
                       update_always=1,
                       props=None)

    vdef = wf.variables['actor']
    vdef.setProperties(description='The ID of the user who performed the last transition',
                       default_value='',
                       default_expr='user/getId',
                       for_catalog=0,
                       for_status=1,
                       update_always=1,
                       props=None)

    vdef = wf.variables['comments']
    vdef.setProperties(description='Comments about the last transition',
                       default_value='',
                       default_expr="python:state_change.kwargs.get('comment', '')",
                       for_catalog=0,
                       for_status=1,
                       update_always=1,
                       props=None)

    vdef = wf.variables['review_history']
    vdef.setProperties(description='Provides access to workflow history',
                       default_value='',
                       default_expr='state_change/getHistory',
                       for_catalog=0,
                       for_status=0,
                       update_always=0,
                       props={'guard_permissions': 'Request review; Review portal content'})

    vdef = wf.variables['time']
    vdef.setProperties(description='Time of the last transition',
                       default_value='',
                       default_expr='state_change/getDateTime',
                       for_catalog=0,
                       for_status=1,
                       update_always=1,
                       props=None)

    # Worklist Initialization
def create_open_policy_workflow(id):
    """Create, setup and return the workflow.
    """
    ob = DCWorkflowDefinition(id)
    setup_open_policy_workflow(ob)
    return ob

addWorkflowFactory(create_open_policy_workflow,
                   id='open_policy_workflow',
                   title='Open Security Policy Workflow')
