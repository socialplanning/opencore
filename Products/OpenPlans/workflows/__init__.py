""" workflows for OpenPlans """
import default
import folder
import teamspace
import teammembership
import closed_teammembership
import member
import team
import policy_open
import policy_medium
import policy_closed
import mship_policy_open
import mship_policy_closed
import open_folder_openplans_workflow
import medium_folder_openplans_workflow
import closed_folder_openplans_workflow

WORKFLOW_MAP = {'plone_openplans_workflow': ('Default OpenPlans Workflow [Plone]',
                                             tuple() ),
                '(Default)': ('', ('OpenRoster',)),
                'open_folder_openplans_workflow': ('Open OpenPlans Folder Workflow [Plone]',
                                              () ),
                'medium_folder_openplans_workflow': ('Medium OpenPlans Folder Workflow [Plone]',
                                              () ),
                'closed_folder_openplans_workflow': ('Closed OpenPlans Folder Workflow [Plone]',
                                              () ),
                'folder_openplans_workflow': ('OpenPlans Folder Workflow [Plone]',
                                              ('Folder', 'Large Plone Folder',) ),
                'openplans_teamspace_workflow': ('OpenPlans Project Workflow',
                                                 ('OpenProject',) ),
                'openplans_team_membership_workflow': ('OpenPlans Team Membership Workflow',
                                                       ('Team Membership',
                                                        'OpenMembership') ),
                'closed_openplans_team_membership_workflow': ('OpenPlans Closed Team Membership Workflow',
                                                       ()),
                'openplans_member_workflow': ('OpenPlans Member Workflow',
                                             ('Member', 'OpenMember',) ),
                'openplans_team_workflow': ('OpenPlans Team Workflow',
                                            ('Team', 'TeamsTool', 'OpenTeam') ),
                'open_policy_workflow': ('Open Security Policy Workflow',
                                             () ),
                'medium_policy_workflow': ('Medium Security Policy Workflow',
                                            () ),
                'closed_policy_workflow': ('Closed Security Policy Workflow',
                                            () ),
                'mship_open_policy_workflow': ('Open Security Membership Policy Workflow',
                                             () ),
                'mship_closed_policy_workflow': ('Closed Security Membership Policy Workflow',
                                            () ),
                }


"""A mapping of placeful workflow policies of the form
{ policy_name :
        { 'title': title,
          'description': description,
          'default': [default workflow chain],
          'types': {type1: [list of wfs,
                    type2: [list of wfs]},
          'context_trans': wf transition that should be applied to context object,
        ),
  ...
}"""
PLACEFUL_POLICIES = {'open_policy': { 'title':       'Open',
                                      'description': "Anyone can view " \
        "content, and any logged in users can edit, add, or delete content.",
                                      'default':     ['open_policy_workflow'],
                                      'types':       {'Folder':['open_folder_openplans_workflow'],
                                                      'Large Plone Folder':['open_folder_openplans_workflow']},
                                      'context_trans':  'open',
                                      'team_policy':    'mship_open_policy',
                                    },
                     'medium_policy': { 'title':     'Medium',
                                      'description': "Anyone can view " \
          "content, but only team members can edit, add, or delete content.",
                                      'default':     ['medium_policy_workflow'],
                                      'types':       {'Folder':['medium_folder_openplans_workflow'],
                                                      'Large Plone Folder':['medium_folder_openplans_workflow']},
                                      'context_trans':  'medium',
                                      'team_policy':    'mship_open_policy',
                                    },
                     'closed_policy': { 'title':     'Closed',
                                      'description': "Only team members " \
          "can view, edit, add, or delete content.",
                                      'default':     ['closed_policy_workflow'],
                                      'types':       {'Folder':['closed_folder_openplans_workflow'],
                                                      'Large Plone Folder':['closed_folder_openplans_workflow']},
                                      'context_trans':  'close',
                                      'team_policy':    'mship_closed_policy',
                                    },
                    }


mship_open_policy = dict(
    title='Open',
    description='Anyone can view',
    default=['openplans_team_membership_workflow'],
    types={'OpenMembership': 'openplans_team_membership_workflow'},
    context_trans='open',
    )

mship_closed_policy = dict(
    title='Closed',
    description='Only team members',
    default=['closed_openplans_team_membership_workflow'],
    types={'OpenMembership': 'closed_openplans_team_membership_workflow'},
    context_trans='close',
    )

MEMBERSHIP_PLACEFUL_POLICIES = dict(
    mship_open_policy=mship_open_policy,
    mship_closed_policy=mship_closed_policy,
    )
