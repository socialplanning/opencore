""" workflows for OpenPlans """


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
    default=['plone_openplans_workflow'],
    types={'OpenMembership': 'openplans_team_membership_workflow'},
    context_trans='open',
    )

mship_closed_policy = dict(
    title='Closed',
    description='Only team members',
    default=['plone_openplans_workflow'],
    types={'OpenMembership': 'closed_openplans_team_membership_workflow'},
    context_trans='close',
    )

MEMBERSHIP_PLACEFUL_POLICIES = dict(
    mship_open_policy=mship_open_policy,
    mship_closed_policy=mship_closed_policy,
    )
