from Products.PlacelessTranslationService.Negotiator import lang_accepted
from pkg_resources import resource_filename
from os import listdir
from zope.i18n.interfaces import IUserPreferredLanguages

# XXX note that this assumes an unzipped egg
def available_languages(use_latest_version=False):
    """ peek into the xinha directory to determine language localizations """

    langs = ['en']
    #        ^^^^ xinha doesn't provide a formal english localization; 
    # instead, if the language is set to 'en', no localization takes place
    # that means we need to inject 'en' into the set of available languages
    # since we won't find it by looking at the translations
    
    if not use_latest_version:
        xinha_l10n_dir = resource_filename('opencore.js', 'thirdparty/xinha/lang')
    else:
        xinha_l10n_dir = resource_filename('opencore.js', 'thirdparty/xinha96/lang')
    # XXX remember to change this if xinha ever moves!

    for file in listdir(xinha_l10n_dir):
        if file.endswith('.js'):
            langs.append(file[:-3])
        #else: what? ignore, i suppose

    return langs


def xinha_lang_code(request, use_latest_version=False):
    """
    Returns the best available language code for clientside
    localization of the Xinha UI, based on the available
    localizations and the user's language preferences
    """

    # opencore.xinha.i18n gives us the available languages
    # (like a zope.i18n.interfaces.ILanguageAvailability)
    #
    # and to figure out the user's language preferences, we might
    # use a zope.i18n.interfaces.IUserPreferredLanguages.
    #
    # this function itself serves the same purpose as an INegotiator;
    # if we used the interface it would look like
    #  getUtility(INegotiator).getLanguage(opencore.xinha.i18n.available_languages(), REQUEST)
    #
    # but the registered request:->IUserPreferredLanguages implementation
    # (which ends up, via Products.Five.i18n:PTSLanguages, being
    # Products.PlacelessTranslationService.Negotiator:getLangPrefs)
    # is somewhat convoluted and involves its own ad hoc registry of
    # IUserPreferredLanguages utilities, which it consults according
    # to its (seemingly not publically mutable) precedence order (as
    # determined at registration time)
    #
    #  * Products.PlacelessTranslationService.Negotiator:BrowserAccept
    #    component, which properly interprets HTTP_ACCEPT_LANGUAGE, is
    #    registered as the fallback implementation, and as of r23476 there
    #    are these higher-precedence components:
    #
    #  * Products.PlacelessTranslationService.Negotiator:CookieAccept
    #    (nonstandard, cookie based) -- I think that in practice we
    #    are not using this at all any more, though the PTS product
    #    is apparently providing us with PO->MO autocompilation on
    #    zope startup:
    #    http://www.openplans.org/projects/opencore/lists/opencore-dev/archive/2008/10/1223483422707
    #
    #  * Products.PloneLanguageTool.LanguageTool:PrefsForPTS (no idea
    #    what this does or how it works from glancing at the code, but
    #    this is probably documented somewhere)
    #
    # The latter wins precedence and calculates the user's preferred
    # language list, but it doesn't seem to respond to the only thing
    # I understand, HTTP's Accept-language.
    #
    # That's just in an OpenCore installation; in customized installations,
    # other translation facilities may be present, and for all I know they
    # might not even use the same core zope.i18n system. IndyCore and
    # OpenFSM already have some "language preference" functionality, so
    # we might want to figure out how that works, to be compatible; start at
    #  1) http://svn.openesf.net/openfsm/trunk/openfsm/browser/topnav/selector.py
    #  2) https://svn.plone.org/svn/plone/plone.app.i18n/trunk/plone/app/i18n/locales/browser/selector.py
    
    lang_prefs = IUserPreferredLanguages(request).getPreferredLanguages()

    # Since we aren't going through a negotiator, we'll just rewrite
    # PTS.Negotiator:Negotiator._negotiate (but simplified, since that
    # implementation generalizes language and content-type negotiations)
    # using our lang_prefs data rather than the getLangPrefs call.
    available_langs = available_languages(use_latest_version)
    for lang in lang_prefs:
        if lang in available_langs:
            return lang
        for available_lang in available_langs:
            # if the client requested pt-br, pt is better than nothing
            if lang_accepted(available_lang, lang):
                return available_lang
    return "en" # xinha seems to treat en as the default language
