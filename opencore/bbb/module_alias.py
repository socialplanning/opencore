# BBB
import sys
import opencore
import opencore.member
import opencore.member.transient_messages
import opencore.member.browser
import opencore.interfaces.member
import opencore.interfaces.bbb
import opencore.browser
import opencore.project
import opencore.project.browser
import opencore.bbb.transient_messages
import wicked
import Products.SimpleAttachment.content.file

def do_aliases():
    sys.modules['opencore.siteui'] = opencore.browser
    #sys.modules['opencore.nui'] = opencore.browser
    sys.modules['opencore.nui.project'] = opencore.project.browser
    sys.modules['opencore.nui.member'] = opencore.member.browser
    sys.modules['opencore.nui.member.transient_messages'] = opencore.bbb.transient_messages
    sys.modules['opencore.nui.member.interfaces'] = opencore.interfaces.bbb
    sys.modules['opencore.nui.project.interfaces'] = opencore.interfaces.bbb
    sys.modules['opencore.siteui.interfaces'] = opencore.interfaces.member

    # wicked BBB crap
    sys.modules['Products.wicked'] = wicked
    sys.modules['Products.wicked.lib'] = wicked
    sys.modules['Products.wicked.lib.cache'] = wicked.cache # for CacheStore obs
    sys.modules['Products.wicked.interfaces'] = wicked.interfaces
    sys.modules['Products.wicked.example'] = wicked.atcontent
    sys.modules['Products.wicked.example.wickeddoc'] = wicked.atcontent.wickeddoc

    # RichDocument -> SimpleAttachment
    sys.modules['Products.RichDocument.content.attachments'] = \
            Products.SimpleAttachment.content.file
