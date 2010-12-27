from opencore.utils import setup
import transaction

app = setup(app)

mh = app.openplans.MailHost

import sys
import pdb

try:
    port = int(sys.argv[-1])
except TypeError:
    port = 25

if not mh.smtp_host:
    mh.smtp_host = "localhost"

print "Setting MailHost to use port %s" % port
    
mh.smtp_port = port
transaction.commit()
