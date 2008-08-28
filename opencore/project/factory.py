from opencore.interfaces.workflow import IWriteWorkflowPolicySupport

def initialize_project(project, request):
    project._createTeam()
    
    # Set initial security policy
    policy = request.get('workflow_policy', None)
    policy_writer = IWriteWorkflowPolicySupport(project)
    if policy_writer is not None:
        policy_writer.setPolicy(policy)
        
    project._createIndexPage() # create the initial "getting started" wiki page

class ProjectFactory(object):

    @classmethod
    def new(self, request, context):
        request.set('__initialize_project__', True)
        
        from Products.CMFCore.utils import getToolByName
        factory_tool = getToolByName(context, 'portal_factory')

        id_ = request.form['projid']
        request.form['title'] = request.form['project_title']

        project = factory_tool.restrictedTraverse('OpenProject/%s' % id_)

        factory_tool.doCreate(project, id_)

        proj = context[id_]

        proj.processForm(metadata=1) # what is this metadata=1?

        initialize_project(proj, request)

        # ugh... roster might have been created by an event before a
        # team was associated (in _initializeProject), need to fix up
        roster_id = proj.objectIds(spec='OpenRoster')
        if roster_id:
            roster = proj._getOb(roster_id[0])
            if not roster.getTeams():
                roster.setTeams(proj.getTeams())
        # @@TODO: ^^^ do we still use OpenRoster at all? i don't think so?

        # we need to remove the Owner role which is assigned to the
        # member who created the project; otherwise the creator will
        # have all administrative privileges even after he leaves
        # the project or is demoted to member.
        owners = proj.users_with_local_role("Owner")
        proj.manage_delLocalRoles(owners)
        # @@ why don't i need to reindex allowed roles and users?

        from zope import event
        from opencore.interfaces.event import AfterProjectAddedEvent
        event.notify(AfterProjectAddedEvent(proj, request))
        return proj
