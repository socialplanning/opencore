

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
