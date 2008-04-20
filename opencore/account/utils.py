from opencore.configuration.utils import product_config

def email_confirmation(is_test=False):
    """get email confirmation mode from zope.conf"""
    if is_test:
        return True
    conf = product_config('email-confirmation', 'opencore.nui')
    if conf:
        val = conf.title()
        if val == 'True':
            return True
        elif val == 'False':
            return False
        else:
            raise ValueError('email-confirmation should be "True" or "False"')
    return True # the default

def turn_confirmation_on():
    email_confirmation.func_defaults = (True,)

def turn_confirmation_off():
    email_confirmation.func_defaults = (False,)
