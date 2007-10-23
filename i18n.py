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
