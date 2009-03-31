from pkg_resources import resource_filename
from os import listdir

# XXX note that this assumes an unzipped egg
def available_languages():
    """ peek into the xinha directory to determine language localizations """

    langs = ['en']
    #        ^^^^ xinha doesn't provide a formal english localization; 
    # instead, if the language is set to 'en', no localization takes place
    # that means we need to inject 'en' into the set of available languages
    # since we won't find it by looking at the translations
    
    xinha_l10n_dir = resource_filename('opencore.js', 'thirdparty/xinha/lang')
    # XXX remember to change this if xinha ever moves!

    for file in listdir(xinha_l10n_dir):
        if file.endswith('.js'):
            langs.append(file[:-3])
        #else: what? ignore, i suppose

    return langs

