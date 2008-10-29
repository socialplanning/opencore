from Products.CMFCore.utils import getToolByName
from opencore.project.handler import _initialize_project
from zope.app.event.objectevent import ObjectCreatedEvent
from zope.event import notify

projects_map = {'p1':{'title':'Project One',},
                'p2':{'title':'Project Two',},
                'p3':{'title':'Project Three',},
                'p4':{'title':'Project Four',},
                }

members_map = {'m1':{'fullname':'Mèmber Oñe',
                     'password':'testy',
                     'email':'notreal1@example.com',
                     'projects': {'p1':tuple(),
                                  'p2':tuple(),
                                  'p3':('ProjectAdmin',),
                                  },
                     },
               'm2':{'fullname':'Mëmber Two',
                     'password':'testy',
                     'email':'notreal2@example.com',
                     'projects': {'p2':tuple(),
                                  'p3':tuple(),
                                  'p4':('ProjectAdmin',),
                                  },
                     },
               'm3':{'fullname':'Mëmber Three',
                     'password':'testy',
                     'email':'notreal3@example.com',
                     'projects': {'p3':tuple(),
                                  'p4':tuple(),
                                  'p1':('ProjectAdmin',),
                                  },
                     },
               'm4':{'fullname':'Mëmber Four',
                     'password':'testy',
                     'email':'notreal4@example.com',
                     'projects': {'p4':tuple(),
                                  'p1':tuple(),
                                  'p2':('ProjectAdmin',),
                                  },
                     },
               }


def create_test_content(self, p_map=projects_map, m_map=members_map):
    """ populates an openplans site w/ dummy test content """
    portal = getToolByName(self, 'portal_url').getPortalObject()

    mdc = getToolByName(self, 'portal_memberdata')
    mdc.unit_test_mode = True # suppress registration emails
    tm_tool = getToolByName(self, 'portal_teams')
    wf_tool = getToolByName(self, 'portal_workflow')
    ms_tool = getToolByName(self, 'portal_membership')
    
    pcontainer = getattr(portal, 'projects', None)
    if pcontainer is None:
        return "ERROR: no 'projects' folder"

    out = []

    for p_id, p_data in p_map.items():
        pcontainer.invokeFactory('OpenProject', p_id, **p_data)
        request = self.REQUEST
        request.form['workflow_policy'] = p_data.get('workflow_policy',
                                                     'medium_policy')
        _initialize_project(getattr(pcontainer, p_id), request)
        out.append('Project %s added' % p_id)

    for mem_id, mem_data in m_map.items():
        member = create_member(self, mem_id, **mem_data)
        out.append('Member %s added' % mem_id)
        projdata = mem_data.get('projects', {})
        for p_id, p_roles in projdata.items():
            team = tm_tool.getTeamById(p_id)
            team.addMember(mem_id)
            
            out.append('-> added to project %s' % p_id)
            mship = team.getMembershipByMemberId(mem_id)
            mship.do_transition('approve_public')
            if p_roles:
                mship.editTeamRoles(p_roles)
                out.append('-> project roles granted: %s' % str(p_roles))

    for team in tm_tool.getTeams():
        if 'admin' in team.objectIds():
            team.removeMember('admin')

    mdc.unit_test_mode = False

    # force w/f security updating
    wftool = getToolByName(self, 'portal_workflow')
    wftool.updateRoleMappings()
    return "\n".join(out)

def create_member(context, mem_id, out=None, **mem_data):
    """creates and confirms a member"""
    mdc = getToolByName(context, 'portal_memberdata')

    # create temp member
    pf = mdc.portal_factory
    id_ = mem_id
    mem_folder = pf._getTempFolder('OpenMember')
    mem = mem_folder.restrictedTraverse('%s' % id_)
    
    # create it for real.
    mem = pf.doCreate(mem, mem_id)
    result = mem.processForm()
    mem.setUserConfirmationCode()
    mem._setPassword(mem_data['password'])
    mem.setEmail(mem_data['email'])
    mem.setFullname(mem_data['fullname'])

    # and confirm it.

    # need to set/delete the attribute for the workflow guards
    setattr(mem, 'isConfirmable', True)
    wftool = getToolByName(context, 'portal_workflow')
    wf_id = 'openplans_member_workflow'
    status = wftool.getStatusOf(wf_id, mem)
    status['review_state'] = 'public'
    wftool.setStatusOf(wf_id, mem, status)
    delattr(mem, 'isConfirmable')

    mem.reindexObject()
    notify(ObjectCreatedEvent(mem))
    ms_tool = getToolByName(context, 'portal_membership')
    ms_tool.createMemberArea(mem.getId())
    return mem
