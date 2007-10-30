"""
config utils
"""

def product_config(variable, namespace, default=''):
    """
    get a variable from the product-config (etc/zope.conf)
    """
    from App import config
    
    try:
        cfg = config.getConfiguration().product_config.get(namespace)
    except AttributeError:
        from warnings import warn
        warn("""Product configuration most likely not loaded""")
        return default
        
    if cfg:
        return cfg.get(variable, default)
    return default
