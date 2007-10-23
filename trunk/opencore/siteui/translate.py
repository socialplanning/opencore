from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from interfaces import ITranslate

class TranslationAdapter(object):
    implements(ITranslate)
    
    def __init__(self, context):
        self.context = context
        self.tool = getToolByName(context, 'translation_service')
        self.asunicodetype = self.tool.asunicodetype
        self.encode = self.tool.encode
    
    def translate(self, msgid, mapping={}, default=None, domain='plone', target_language=None, escape_for_js=False):
        # NOTE: using this script means you ignore unicode and hope
        #       that the system will handle that for you. Use the
        #       utranslate script and use unicode type instead of string type.

        # make sure the mapping contains unicode type strings
        # as the caller does not care about encoding we dont care about errors
        # we also assume that passed strings are encoded with the site encoding
        for k, v in mapping.items():
            if isinstance(v, str):
                mapping[k]=self.asunicodetype(v, errors='replace')

        # translate using unicode type
        value = self.utranslate(msgid, mapping, default, domain, target_language)

        # encode using site encoding
        result=self.encode(value)

        if escape_for_js:
            return result.replace("'", "\\'")
        else:
            return result

    __call__ = translate
    
    def utranslate(self, msgid, mapping={}, default=None, domain='plone', target_language=None):
        if msgid == None:
            return None

        # this returns type unicode 
        value = self.tool.utranslate(domain,
                                     msgid,
                                     mapping,
                                     context=self.context,
                                     target_language=target_language,
                                     default=default)

        if not value and default is None:
            value = msgid

        for k, v in mapping.items():
            value = value.replace('${%s}' % k, v)

        return value

class TranslationView(BrowserView, TranslationAdapter):
    """
    view class for access translation info
    """
    implements(ITranslate)
    
    __call__ = TranslationAdapter.__call__

    def __init__(self, context, REQUEST):
        self.request = REQUEST
        TranslationAdapter.__init__(self, context)
