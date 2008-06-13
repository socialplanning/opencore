"""
Override the default index im/exporters so the indexes and lexicons
don't get cleared every single time.

See https://bugs.launchpad.net/zope-cmf/+bug/161682
"""

from BTrees.IOBTree import IOBTree
from BTrees.Length import Length
from BTrees.OIBTree import OIBTree
from Products.GenericSetup.PluginIndexes.exportimport \
     import PluggableIndexNodeAdapter as PluggableIndexNodeAdapterBase
from Products.GenericSetup.PluginIndexes.exportimport \
     import DateIndexNodeAdapter as DateIndexNodeAdapterBase
from Products.GenericSetup.PluginIndexes.exportimport \
     import DateRangeIndexNodeAdapter as DateRangeIndexNodeAdapterBase
from Products.GenericSetup.ZCTextIndex.exportimport \
     import ZCTextIndexNodeAdapter as ZCTextIndexNodeAdapterBase
from Products.GenericSetup.ZCTextIndex.exportimport \
     import ZCLexiconNodeAdapter as ZCLexiconNodeAdapterBase

from Products.ZCTextIndex.PipelineFactory import element_factory
from Products.ZCTextIndex.ZCTextIndex import index_types

def clearIfChanged(fun):
    """
    Decorator which wraps index and lexicon importers, will cause
    them to be cleared only if the config changes.
    """
    def importNode(self, node):
        before = self.node.toxml()
        fun(self, node)
        if before != self.node.toxml():
            try:
                # index?
                self.context.clear()
            except AttributeError:
                # nope, it's a lexicon
                self.context._wids = OIBTree()
                self.context._words = IOBTree()
                self.context.length = Length()
    return importNode


class PluggableIndexNodeAdapter(PluggableIndexNodeAdapterBase):
    """
    FieldIndex, KeywordIndex im/exporter 
    """
    @clearIfChanged
    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        indexed_attrs = []
        for child in node.childNodes:
            if child.nodeName == 'indexed_attr':
                indexed_attrs.append(
                                  child.getAttribute('value').encode('utf-8'))
        self.context.indexed_attrs = indexed_attrs

    node = property(PluggableIndexNodeAdapterBase._exportNode, _importNode)

 
class DateIndexNodeAdapter(DateIndexNodeAdapterBase):
    """
    DateIndex im/exporter
    """
    @clearIfChanged
    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProperties()

        self._initProperties(node)

    node = property(DateIndexNodeAdapterBase._exportNode, _importNode)


class DateRangeIndexNodeAdapter(DateRangeIndexNodeAdapterBase):
    """
    DateIndex im/exporter
    """
    @clearIfChanged
    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        self.context._edit(node.getAttribute('since_field').encode('utf-8'),
                           node.getAttribute('until_field').encode('utf-8'))

    node = property(DateRangeIndexNodeAdapterBase._exportNode, _importNode)


class ZCTextIndexNodeAdapter(ZCTextIndexNodeAdapterBase):

    """Node im- and exporter for ZCTextIndex.
    """
    @clearIfChanged
    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        index = self.context
        indexed_attrs = []
        
        for child in node.childNodes:
            if child.nodeName == 'indexed_attr':
                indexed_attrs.append(
                                  child.getAttribute('value').encode('utf-8'))
            elif child.nodeName == 'extra':
                name = child.getAttribute('name')
                if name == 'index_type':
                    index_type = child.getAttribute('value')
                    index._index_factory = index_types[index_type]
                    index._index_type = index_type
                elif name == 'lexicon_id':
                    pass # XXX

        self.context._indexed_attrs = indexed_attrs

    node = property(ZCTextIndexNodeAdapterBase._exportNode, _importNode)


class ZCLexiconNodeAdapter(ZCLexiconNodeAdapterBase):
    """Node im- and exporter for ZCTextIndex Lexicon.
    """
    @clearIfChanged
    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        pipeline = []
        for child in node.childNodes:
            if child.nodeName == 'element':
                element = element_factory.instantiate(
                      child.getAttribute('group').encode('utf-8'),
                      child.getAttribute('name').encode('utf-8'))
                pipeline.append(element)
        self.context._pipeline = tuple(pipeline)

    node = property(ZCLexiconNodeAdapterBase._exportNode, _importNode)
