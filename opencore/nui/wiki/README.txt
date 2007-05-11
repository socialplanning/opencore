=========
 wiki ui
=========

    >>> page_id = self.portal.projects.p1.getDefaultPage()
    >>> page = getattr(self.portal.projects.p1, page_id)

Test wiki page registrations::

    >>> page.restrictedTraverse('@@index.html')
    <...SimpleViewClass from ...wiki/wiki-view.pt object at ...>
    
    >>> page.restrictedTraverse('@@wiki_macros')
    <...SimpleViewClass ...wiki/wiki_macros.pt object at ...>
    
    >>> page.restrictedTraverse('@@update-test')
    <...SimpleViewClass ...wiki/update-test.pt object at ...>    
    
    >>> page.restrictedTraverse('@@edit')
    <...SimpleViewClass from ...wiki/wiki-edit.pt object at ...>
    
    >>> page.restrictedTraverse('@@edit-nick')
    <...SimpleViewClass from ...wiki/wiki-edit-nick.pt object at ...>

Test wiki attachment registrations::

    >>> page.restrictedTraverse('@@updateAtt')
    <...SimpleViewClass from ...wiki/ ...>

    >>> page.restrictedTraverse('@@createAtt')    
    <...SimpleViewClass from ...wiki/ ...>

    >>> page.restrictedTraverse('@@deleteAtt')    
    <...SimpleViewClass from ...wiki/ ...>
