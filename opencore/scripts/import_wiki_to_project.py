from opencore.utils import setup
import transaction
import os, sys
from zipfile import ZipFile

app = setup(app)

zipfile = sys.argv[-2]
project = sys.argv[-1]

project = app.openplans.projects[project]
proj_id = project.getId()

zipfile = ZipFile(zipfile)

import tempfile
tempdir = tempfile.mkdtemp(prefix="--opencore-wiki-import-")

for path in zipfile.namelist():
    parts = path.split("/")
    if len(parts) < 2:
        continue
    if parts[1] == "wiki_history":
        if path.endswith("/"):
            try:
                os.makedirs(os.path.join(tempdir, *parts[2:]))
            except:
                pass
            continue
        else:
            try:
                os.makedirs(os.path.join(tempdir, *parts[2:-1]))
            except:
                pass
        f = zipfile.read(path)
        fp = open(os.path.join(tempdir, *parts[2:]), 'w')
        try:
            fp.write(f)
        finally:
            fp.close()

print tempdir
