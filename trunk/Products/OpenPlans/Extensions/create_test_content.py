import sys
from Products.CMFCore.utils import getToolByName
from opencore.project.handler import _initialize_project

projects_map = {'p1':{'title':'Project One',},
                'p2':{'title':'Project Two',},
                'p3':{'title':'Project Three',},
                'p4':{'title':'Project Four',},
                }

members_map = {'m1':{'fullname':'Member One',
                     'password':'testy',
                     'email':'notreal1@example.com',
                     'projects': {'p1':tuple(),
                                  'p2':tuple(),
                                  'p3':('ProjectAdmin',),
                                  },
                     },
               'm2':{'fullname':'Member Two',
                     'password':'testy',
                     'email':'notreal2@example.com',
                     'projects': {'p2':tuple(),
                                  'p3':tuple(),
                                  'p4':('ProjectAdmin',),
                                  },
                     },
               'm3':{'fullname':'Member Three',
                     'password':'testy',
                     'email':'notreal3@example.com',
                     'projects': {'p3':tuple(),
                                  'p4':tuple(),
                                  'p1':('ProjectAdmin',),
                                  },
                     },
               'm4':{'fullname':'Member Four',
                     'password':'testy',
                     'email':'notreal4@example.com',
                     'projects': {'p4':tuple(),
                                  'p1':tuple(),
                                  'p2':('ProjectAdmin',),
                                  },
                     },
               }



def create_test_content(self, p_map=None, m_map=None):
    """ populates an openplans site w/ dummy test content """
    portal = getToolByName(self, 'portal_url').getPortalObject()

    # XXX this shouldn't be necessary, as its already set in install
    # XXX this should probably be removed
    # from Products.OpenPlans import config
    # portal.manage_changeProperties(email_from_address=config.SITE_FROM_ADDRESS)

    mdc = getToolByName(self, 'portal_memberdata')
    mdc.unit_test_mode = True # suppress registration emails
    tm_tool = getToolByName(self, 'portal_teams')
    wf_tool = getToolByName(self, 'portal_workflow')
    ms_tool = getToolByName(self, 'portal_membership')

    if p_map is None:
        p_map = projects_map
    if m_map is None:
        m_map = members_map
    
    pcontainer = getattr(portal, 'projects', None)
    if pcontainer is None:
        return "ERROR: no 'projects' folder"

    out = []

    for p_id, p_data in p_map.items():
        pcontainer.invokeFactory('OpenProject', p_id, **p_data)
        request = self.REQUEST
        request.form['workflow_policy'] = 'medium_policy'
        _initialize_project(getattr(pcontainer, p_id), request)
        out.append('Project %s added' % p_id)

    for mem_id, mem_data in m_map.items():
        mdc.invokeFactory('OpenMember', mem_id, **mem_data)
        mem = mdc._getOb(mem_id)
        mem._setPassword(mem_data['password'])
        mem.fixOwnership()
        mem.isConfirmable = True
        wf_tool.doActionFor(mem, 'register_public')
        del mem.isConfirmable

        # create the member area and mark it with the appropriate interface
        # ms_tool.createMemberArea(mem_id)
        # do_create_home_directory(mem, {}, 'worthless text')

        out.append('Member %s added' % mem_id)
        for p_id, p_roles in mem_data['projects'].items():
            team = tm_tool.getTeamById(p_id)
            team.addMember(mem_id)
            out.append('-> added to project %s' % p_id)
            mship = team.getMembershipByMemberId(mem_id)
            wf_tool.doActionFor(mship, 'approve_public')
            if p_roles:
                mship.editTeamRoles(p_roles)
                out.append('-> project roles granted: %s' % str(p_roles))

    mdc.unit_test_mode = False
    return "\n".join(out)
