import os

from zope.interface import Interface
from zope.schema import TextLine
from zope.configuration.exceptions import ConfigurationError
from zope.configuration.fields import Path, GlobalInterface, GlobalObject
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.security.zcml import Permission

class ISearchViewDirective(Interface):
    """ 
    Register an OpenCore SearchView browser view for contexts of the given interface.
    
    The directive accepts most of the standard browser:page arguments: `for`,
    `permission`, `class`, `name` and `template`. If no class factory is set,
    the view will be implemented with `opencore.nui.search.SearchView` which
    provides basic searching functionality by returning all viewable contents
    published within the current context.

    Though you can render a custom template with the `template` argument, the
    default opencore/nui/main/searchresults.pt template should suffice for most
    simple cases. That template calls out to several others which can be
    individually customized with this directive:

     * The `result_listing` template defines how an individual search result
       is rendered.  If you do not set a template here, the default template,
       opencore/nui/main/searchresults-resultlist.pt, will be used.

     * The `sort_string` template defines the search result summary text. Its
       default implementation is opencore/nui/main/searchresults-sortstring.pt

     * The `sortable_fields` template defines the fields which users can use to
       sort their search results, which are rendered in the "sort by" dropdown
       in the standard template. By default, results can be sorted by id, creator
       or content type (opencore/nui/main/searchresults-sortablefields.pt).
       This template should be structured as an HTML <UL>, with each sorting
       option in its own <LI>. The `id` of the <LI> should be the attribute name
       that you want to sort by, and its content should be a human-readable string.
    """

    for_ = GlobalInterface(
        title=u"The interface this view is for.",
        required=False
        )

    permission = Permission(
        title=u"Permission",
        description=u"The permission needed to use the view.",
        required=True
        )

    class_ = GlobalObject(
        title=u"Class",
        description=u"""
        A class to be used as a factory for creating new objects""",
        required=False
        )

    name = TextLine(
        title=u"The name of the page (view)",
        description=u"""
        The name shows up in URLs/paths. For example 'foo' or
        'foo.html'. This attribute is required.""",
        required=True
        )

    template = Path(
        title=u"The name of a template that implements the page.",
        description=u"""
        Refers to a file containing a page template (should end in
        extension '.pt' or '.html').""",
        required=False
        )

    result_listing = Path(
        title=u"The name of a template that can render a single result.",
        description=u"""
        Refers to a file containing a page template (should end in
        extension '.pt' or '.html').""",
        required=False
        )

    sortable_fields = Path(
        title=u"The name of a template that can render a single result.",
        description=u"""
        Refers to a file containing a page template (should end in
        extension '.pt' or '.html').""",
        required=False
        )

    sort_string = Path(
        title=u"The name of a template that can render a single result.",
        description=u"""
        Refers to a file containing a page template (should end in
        extension '.pt' or '.html').""",
        required=False
        )

from Products.Five.browser.metaconfigure import page
from opencore.nui.main import search
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
import os

def factory(_context, name, permission, for_,
            layer=IDefaultBrowserLayer,
            template=None, class_=None,
            allowed_interface=None, allowed_attributes=None,
            result_listing=None, sortable_fields=None,
            sort_string=None
            ):

    if class_ is None:
        class_ = search.SearchView

    from pkg_resources import resource_filename
    default_path = 'opencore.nui.main.search'

    if template is None:
        template = resource_filename(default_path,
                                     search.SearchView.default_template)
    if result_listing is None:
        result_listing = resource_filename(default_path, 
                                           search.SearchView.default_result_listing)
    if sortable_fields is None:
        sortable_fields = resource_filename(default_path,
                                            search.SearchView.default_sortable_fields)
    if sort_string is None:
        sort_string = resource_filename(default_path,
                                        search.SearchView.default_sort_string)

    if not os.path.isfile(result_listing):
        raise ConfigurationError("No such file", result_listing)

    if not os.path.isfile(sortable_fields):
        raise ConfigurationError("No such file", sortable_fields)

    if not os.path.isfile(sort_string):
        raise ConfigurationError("No such file", sort_string)

    setattr(class_, '_result_listing', ZopeTwoPageTemplateFile(result_listing))
    setattr(class_, '_sortable_fields', ZopeTwoPageTemplateFile(sortable_fields))
    setattr(class_, '_sort_string', ZopeTwoPageTemplateFile(sort_string))

    page(_context, name, permission, for_,
         layer=layer, template=template, class_=class_,
         allowed_interface=allowed_interface,
         allowed_attributes=allowed_attributes)         
    
