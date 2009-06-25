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

    # if no translation is available in the desired language,
    # and no default is specified, use the english translation
    # as a fallback; better that than "email_to_pending_user"
    if default is None:
        default_kw = dict(kw)
        default_kw['target_language'] = 'en'

        if isinstance(msgid, zope.i18nmessageid.Message):
            # Messages have a read-only mapping; we can make a copy to stuff
            # our mapping in there.

            # msgid.domain may return None; if it does, TranslationDomain.translate
            # will clobber its own translation domain with None from the msgid object,
            # and then we'll get a component lookup error (luckily we have a test in
            # opencore/utility/email-sender.txt L39 that managed to trip this wire)
            msgid = zope.i18nmessageid.Message(msgid, domain=i18n_domain)

        default = getUtility(ITranslationDomain,
                             i18n_domain).translate(msgid, **default_kw)
        # zope.i18n.translationdomain:TranslationDomain.translate says
        # that MessageID attributes override arguments, so it's safe to
        # just stuff these all in, i think
        kw['default'] = default

        # Products.Five.i18n @L38 clobbers kw['default'] with msgid.default
        # so we need to trick it.
        if isinstance(msgid, zope.i18nmessageid.Message):
            # Messages have a read-only mapping; we can make a copy to stuff
            # our mapping in there.
            msgid = zope.i18nmessageid.Message(msgid, default=default)

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


# everything below this comment, and the corresponding registration 
# in opencore.configuration's meta.zcml, should be discarded by
# upgrading zope.i18n as soon as possible.
from zope.i18n.translationdomain import TranslationDomain
class ProjectNounAwareTranslationDomain(TranslationDomain):
    """
    a thin wrapper around default TranslationDomain component
    that injects appropriate translation for msgid `project_noun`
    into all translations (except when translating `project_noun`
    of course)

    intended to be registered as an override. when opencore
    upgrades to a more recent version of zope.i18n with the
    recursive translation feature, this should be discarded.
    """

    def translate(self, msgid, mapping=None, context=None,
                  target_language=None, default=None):
        if msgid == "project_noun":
            noun = TranslationDomain.translate(
                self, msgid, mapping, context, target_language, default)
            return noun

        mapping = mapping or {}

        # defer import to circumvent loops
        from opencore.project.utils import project_noun

        mapping['project_noun'] = project_noun()

        if isinstance(msgid, zope.i18nmessageid.Message) and msgid.mapping:
            combined_mapping = dict(mapping)
            combined_mapping.update(msgid.mapping)
            msgid = zope.i18nmessageid.Message(msgid, mapping=combined_mapping)
            
        return TranslationDomain.translate(
            self, msgid, mapping, context, target_language, default)


# fork of same-named function in zope/i18n/zcml.py 
import os
from zope.i18n.gettextmessagecatalog import GettextMessageCatalog
from zope.component.zcml import utility
from zope.i18n.interfaces import ITranslationDomain
from zope.i18n.testmessagecatalog import TestMessageCatalog
import zope.i18nmessageid
def registerTranslations(_context, directory):

    path = os.path.normpath(directory)
    domains = {}

    # Gettext has the domain-specific catalogs inside the language directory,
    # which is exactly the opposite as we need it. So create a dictionary that
    # reverses the nesting.
    for language in os.listdir(path):
        lc_messages_path = os.path.join(path, language, 'LC_MESSAGES')
        if os.path.isdir(lc_messages_path):
            for domain_file in os.listdir(lc_messages_path):
                if domain_file.endswith('.mo'):
                    domain_path = os.path.join(lc_messages_path, domain_file)
                    domain = domain_file[:-3]
                    if not domain in domains:
                        domains[domain] = {}
                    domains[domain][language] = domain_path

    # Now create TranslationDomain objects and add them as utilities
    for name, langs in domains.items():
        domain = ProjectNounAwareTranslationDomain(name)

        for lang, file in langs.items():
            domain.addCatalog(GettextMessageCatalog(lang, name, file))

        # make sure we have a TEST catalog for each domain:
        domain.addCatalog(TestMessageCatalog(name))

        utility(_context, ITranslationDomain, domain, name=name)
#
