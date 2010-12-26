from opencore.utils import setup
import transaction

app = setup(app)

mh = app.openplans.MailHost

import sys
import pdb
try:
    port = int(sys.argv[2])
except:
    port = 25

if not mh.smtp_host:
    mh.smtp_host = "localhost"
    
mh.smtp_port = port
transaction.commit()
