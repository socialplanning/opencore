from lxml import etree

from Acquisition import aq_base
from Products.GenericSetup.utils import _resolveDottedName
from Products.GenericSetup.tool import TOOLSET_XML
from Products.Archetypes.utils import OrderedDict


def importToolset(context):

    """
    Import tools from XML file.  We don't use GenericSetup's b/c it
    sorts the tools alphabetically by name.  The sorting happens in
    the toolset registry; we let that happen, but we perform the import
    based on the order in the XML file.
    """
    site = context.getSite()
    encoding = context.getEncoding()
    logger = context.getLogger('mdtool')

    xml = context.readDataFile(TOOLSET_XML)
    if xml is None:
        logger.info('Nothing to import.')
        return

    setup_tool = context.getSetupTool()
    toolset = setup_tool.getToolsetRegistry()

    # we still let the persistent registry store the info
    toolset.parseXML(xml, encoding)

    # but we generate our own copy that retains the order from the
    # file
    ts = etree.fromstring(xml)

    existing_ids = site.objectIds()
    existing_values = site.objectValues()

    for tool_id in toolset.listForbiddenTools():

        if tool_id in existing_ids:
            site._delObject(tool_id)

    for required in ts.xpath('//required'):
        info = required.attrib
        tool_id = str(info['tool_id'])
        tool_class = _resolveDottedName(info['class'])

        existing = getattr(aq_base(site), tool_id, None)
        try:
            new_tool = tool_class()
        except TypeError:
            new_tool = tool_class(tool_id)
        else:
            try:
                new_tool._setId(tool_id)
            except: # XXX:  ImmutableId raises result of calling MessageDialog
                pass

        if existing is None:
            site._setObject(tool_id, new_tool)

        else:
            unwrapped = aq_base(existing)
            if not isinstance(unwrapped, tool_class):
                site._delObject(tool_id)
                site._setObject(tool_id, tool_class())

    logger.info('MemberData tool imported.')
