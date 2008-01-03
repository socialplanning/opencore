import sys
from Products.CMFCore.utils import getToolByName
from opencore.project.handler import _initialize_project
from zope.app.event.objectevent import ObjectCreatedEvent
from zope.event import notify

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
        request.form['workflow_policy'] = p_data.get('workflow_policy',
                                                     'medium_policy')
        _initialize_project(getattr(pcontainer, p_id), request)
        out.append('Project %s added' % p_id)

    pf = mdc.portal_factory

    for mem_id, mem_data in m_map.items():
        id_ = mem_id
        mem_folder = pf._getTempFolder('OpenMember')
        mem = mem_folder.restrictedTraverse('%s' % id_)
        
        # now we have mem, a temp member. create it for real.
        mem = pf.doCreate(mem, mem_id)
        result = mem.processForm()
        mem.setUserConfirmationCode()
        mem._setPassword(mem_data['password'])
        mem.setEmail(mem_data['email'])
        mem.setFullname(mem_data['fullname'])

        #and confirm it.
        
        # need to set/delete the attribute for the workflow guards
        setattr(mem, 'isConfirmable', True)
        status = wf_tool.getStatusOf('openplans_member_workflow', mem)
        status ['review_state'] = 'public'
        wf_tool.setStatusOf('openplans_member_workflow', mem, status)
        delattr(mem, 'isConfirmable')

        mem.reindexObject()
        notify(ObjectCreatedEvent(mem))

        ms_tool.createMemberArea(mem.getId())

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
