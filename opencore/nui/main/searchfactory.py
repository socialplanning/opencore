import os

from zope.interface import Interface
from zope.schema import TextLine
from zope.configuration.fields import Path, GlobalInterface, GlobalObject
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.security.zcml import Permission

class ISearchViewDirective(Interface):
    """ whee """

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

    default_path = search.__file__.split(os.path.sep)[:-1]

    if template is None:
        template = search.SearchView.default_template
        template = os.sep + os.path.join(*default_path + [template])
    if result_listing is None:
        result_listing = os.sep + os.path.join(*default_path + [search.SearchView.default_result_listing])
    if sortable_fields is None:
        sortable_fields = os.sep + os.path.join(*default_path + [search.SearchView.default_sortable_fields])
    if sort_string is None:
        sort_string = os.sep + os.path.join(*default_path + [search.SearchView.default_sort_string])

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
    
