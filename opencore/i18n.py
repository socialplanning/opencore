i18n_domain = 'opencore'

import zope.i18nmessageid
_ = zope.i18nmessageid.MessageFactory(i18n_domain)

from Products.CMFPlone.i18nl10n import utranslate

def translate(msgid, domain=i18n_domain, mapping=None, context=None,
              target_language=None, default=None):
    """
    Wrapper around Plone's utranslate method that defaults to the
    our standard domain.  Returns instance of unicode type. 
    """
    kw = dict(mapping=mapping, context=context,
              target_language=target_language, default=default)
    return utranslate(domain, msgid, **kw)

from zope.component import getUtility
from zope.i18n.interfaces import ITranslationDomain
def available_languages():
    """ returns an unordered list like ['en', 'fr', 'br-pt'] """
    
    # we look up the ITranslationDomain utility for the "opencore"
    # i18n domain to ask it what languages it provides translations for,
    # per zope.i18n.translationdomain:TranslationDomain.translate
    #
    # i'm not sure why this isn't an interface method on ITranslationDomain
    # or alternatively why we can't lookup-or-adaptto ILanguageAvailability
    # (maybe see http://www.mail-archive.com/zope3-dev@zope.org/msg05649.html)

    util = getUtility(ITranslationDomain, i18n_domain)
    return util.getCatalogsInfo.keys()

