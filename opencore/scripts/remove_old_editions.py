import sys
import transaction
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SpecialUsers import system
from Products.CMFCore.utils import getToolByName

try:
    portal = sys.argv[1]
except IndexError:
    portal = 'openplans'


portal = getattr(app, portal)
wf = getToolByName(portal,'portal_workflow')
cat = getToolByName(portal,'portal_catalog')
storage = getToolByName(portal,'portal_repository')
content = cat(Language='all')
total=len(content)
skipped = 0
purged = [0,0]
current=0

for obj in content:
    current+=1
    if current%10 == 0:
        print "%f%% %d more to go" % (((100.0*current)/total),total - current)
    try:
        length = storage.getHistory(obj,countPurged=False)._length
        if not length or length < 2:
            print "skipping %s" % obj.getPath()
            skipped+=1
        else:
            print "purging %s revisions from %s" % (length-1,obj.getPath())
            purged[0]+=1
            while storage.getHistory(obj,countPurged=False)._length > 1:
                storage.purge(obj,0,comment="autopurge",countPurged=False)
                purged[1]+=1 
    except:
        import pdb; pdb.set_trace()    
            
print "purged %s revisions from %s objects, skipped %s objects" % (purged[1],purged[0],skipped)


