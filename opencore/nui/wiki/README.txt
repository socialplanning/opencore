=========
 wiki ui
=========

    >>> page_id = self.portal.projects.p1.getDefaultPage()
    >>> page = getattr(self.portal.projects.p1, page_id)

Registrations
=============

Test wiki page registrations::

    >>> page.restrictedTraverse('@@index.html')
    <...SimpleViewClass from ...wiki/wiki-view.pt object at ...>
    
    >>> page.restrictedTraverse('@@wiki_macros')
    <...SimpleViewClass ...wiki/wiki_macros.pt object at ...>
    
    >>> page.restrictedTraverse('@@update-test')
    <...SimpleViewClass from ...wiki/update-test.pt object at ...>
    
    >>> page.restrictedTraverse('@@edit')
    <...SimpleViewClass from ...wiki/wiki-edit.pt object at ...>
    
    >>> page.restrictedTraverse('@@edit-nick')
    <...SimpleViewClass from ...wiki/wiki-edit-nick.pt object at ...>

Test wiki attachment registrations::

    >>> page.restrictedTraverse('@@updateAtt')
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access '@@updateAtt' in this context

    >>> page.restrictedTraverse('@@createAtt')    
    <...SimpleViewClass from ...wiki/create-att.pt object at ...>

    >>> page.restrictedTraverse('@@deleteAtt')    
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access '@@deleteAtt' in this context
