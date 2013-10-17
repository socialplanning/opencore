from zipfile import ZipFile
import sys
import simplejson as json
from opencore.utils import setup
import transaction

app = setup(app)

log_fp = open(sys.argv[-1])
log = log_fp.read()
log_fp.close()

log = log.splitlines()
for project in log:

    print project

    project = json.loads(project)

    zipfilename = project['export']
    zipfile = open(zipfilename, 'rb')
    zipfile = ZipFile(zipfile)

    project = project['project']

    settings = zipfile.read("%s/project/settings.ini" % project)

    parsed_settings = {'description': ""}
    reading_description = False
    for line in settings.splitlines(): #@@TODO make this less stupid
        line = line.strip()
        if reading_description:
            parsed_settings['description'] += line
        if line.startswith("title = "):
            parsed_settings['title'] = line[len("title = "):].strip()
        elif line.startswith("security_policy = "):
            parsed_settings['security_policy'] = line[len("security_policy = "):].strip()
        elif line.startswith("homepage = "):
            parsed_settings['homepage'] = line[len("homepage = "):].strip()
        elif line == "[description]":
            reading_description = True

    from opencore.scripts import (create_one_project, 
                                  import_wiki_to_project,
                                  import_lists_to_project)

    if app.openplans.projects.has_key(project):
        print "Project %s already exists; skipping..." % project
        continue

    create_one_project.main(
        app, project,
        parsed_settings['security_policy'], parsed_settings['title'], 
        parsed_settings['description'])
    print "Importing lists..."
    import_lists_to_project.main(app, zipfilename, project)
    
    print "Importing wiki..."
    import_wiki_to_project.main(app, zipfilename, project)
    
    transaction.commit()
    print "Finished import of project %s" % project

from zope.app.component.hooks import setSite
setSite(app.openplans)
cat = app.openplans.portal_catalog
cat.clearFindAndRebuild()
transaction.commit()
