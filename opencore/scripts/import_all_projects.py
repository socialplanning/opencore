from zipfile import ZipFile
import sys
import simplejson as json

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

    print settings

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

    import subprocess
    ret = subprocess.call(["zope/bin/zopectl", "run", "src/opencore/opencore/scripts/create_one_project.py", project, parsed_settings['security_policy'], parsed_settings['title'], parsed_settings['description']])
    assert ret == 0, ret
    ret = subprocess.call(["zope/bin/zopectl", "run", "src/opencore/opencore/scripts/import_wiki_to_project.py", zipfilename, project])
    assert ret == 0, ret
    ret = subprocess.call(["zope/bin/zopectl", "run", "src/opencore/opencore/scripts/import_lists_to_project.py", zipfilename, project])
    assert ret == 0, ret
    
