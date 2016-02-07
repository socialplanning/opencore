from zipfile import ZipFile
import sys
import simplejson as json
from opencore.utils import setup
import transaction
import csv, sys, os

app = setup(app)

fp = open(sys.argv[-1])
data = csv.reader(fp)

from opencore.scripts.import_one_member_data import main as import_one
i=0
header = data.next()
for member in data:
    i += 1
    member = dict(zip(header, member))

    member_id = member['member_id']
    zipfile = member['export_zipfile']
    status = member['is_confirmed']

    if status != 'confirmed' or not zipfile:
        continue

    import_one(app, zipfile, member_id)
    print "Finished importing %s" % member_id

    if i % 50 == 0:
        transaction.commit
transaction.commit()
