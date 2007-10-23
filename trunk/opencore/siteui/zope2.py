from config import SKINS_DIR, GLOBALS

def initialize(context):
    from Products.CMFCore.DirectoryView import registerDirectory
    registerDirectory(SKINS_DIR, GLOBALS)     

    
