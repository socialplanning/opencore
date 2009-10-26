from zope.component import ComponentLookupError

i18n_domain = 'opencore'

import zope.i18nmessageid
_ = zope.i18nmessageid.MessageFactory(i18n_domain)
from zope.i18nmessageid import Message

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
    if default is None and getattr(msgid, 'default', None) is None:
        try:
            translator = getUtility(ITranslationDomain, i18n_domain)
        except ComponentLookupError:
            # in a fresh build, MO files will not yet have been compiled,
            # so it's possible that we won't find an ITranslationDomain
            # (notably in buildbot builds!). there's no reason to *force*
            # the existence of an English PO file so in that case we'll
            # revert to the default behavior for defaults.
            # http://www.coactivate.org/projects/opencore/lists/opencore-dev/archive/2009/06/1245964042046/forum_view#1246051875766
            return utranslate(domain, msgid, **kw)

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

        default = translator.translate(msgid, **default_kw)
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

    ...but it can't be registered as an override, because the
    `registerTranslations` directive initializes and registers
    TranslationDomain objects directly instead of using ZCA
    component lookup (actually there doesn't seem to be any
    factory component so i'm not sure how else to do it) ..
    so instead we'll register an override of `registerTranslations`
    (below) which forks the original to register these guys.
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
# which also incorporates PTS's monkeypatch thereof,
# to auto-compile translations. _that_ can go away
# if we upgrade to zope.i18n>=3.5.0 according to pw

from zope.i18n.zcml import registerTranslations as register_translations

from Products.PlacelessTranslationService.load import _compile_locales_dir

def registerTranslations(_context, directory):

    # here's that PTS monkeypatch
    _compile_locales_dir(directory)
    # end PTS monkeypatch

    register_translations(_context, directory,
                          _factory=ProjectNounAwareTranslationDomain)

