import roster
import page
import member
import membership

# BBB sys.modules hack to support old location for persistent
#     objects
import sys
sys.modules['Products.OpenPlans.content.membership'] = membership

