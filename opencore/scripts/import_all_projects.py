from zipfile import ZipFile
import sys
import simplejson as json
from opencore.utils import setup
import transaction

app = setup(app)

log_fp = open(sys.argv[-1])
log = log_fp.read()
log_fp.close()

from ConfigParser import RawConfigParser
from StringIO import StringIO

log = log.splitlines()
for project in log:

    print project

    project = json.loads(project)

    zipfilename = project['export']
    zipfile = open(zipfilename, 'rb')
    zipfile = ZipFile(zipfile)

    project = project['project']

    settings = StringIO(zipfile.read("%s/project/settings.ini" % project))
    parsed_settings = RawConfigParser()
    parsed_settings.readfp(settings)

    team_data = json.loads(zipfile.read("%s/project/team.json" % project))

    from opencore.scripts import (create_one_project, 
                                  import_wiki_to_project,
                                  import_lists_to_project)

    if app.openplans.projects.has_key(project):
        print "Project %s already exists; skipping..." % project
        continue

    project_description = zipfile.read("%s/project/description.txt" % project)

    create_one_project.main(
        app, project, team_data, parsed_settings, project_description,
        )
    print "Importing lists..."
    import_lists_to_project.main(app, zipfilename, project)
    
    print "Importing wiki..."
    import_wiki_to_project.main(app, zipfilename, project)
    
    transaction.commit()
    print "Finished import of project %s" % project

from zope.app.component.hooks import setSite
setSite(app.openplans)
cat = app.openplans.portal_catalog
#cat.clearFindAndRebuild()
transaction.commit()
