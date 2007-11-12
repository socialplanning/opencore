# BBB
import sys
import opencore.member
#import opencore.member.browser
import opencore.interfaces.member
import opencore.interfaces.bbb
import opencore.browser
import opencore.project.browser
sys.modules['opencore.siteui'] = opencore.browser
#sys.modules['opencore.nui'] = opencore.browser
sys.modules['opencore.nui.project'] = opencore.project.browser
#sys.modules['opencore.nui.member'] = opencore.member.browser
sys.modules['opencore.nui.member.interfaces'] = opencore.interfaces.bbb
sys.modules['opencore.nui.project.interfaces'] = opencore.interfaces.bbb
sys.modules['opencore.siteui.interfaces'] = opencore.interfaces.member

del sys
