from sven.bzr import BzrAccess
from datetime import datetime

def repo(project_id):
    return BzrAccess("/tmp/opencorebzr/projects/%s/" % project_id)

def get_versions(project_id, page_id):
    versions = []
    log = repo.log(id)
    for x in range(len(log)):
        version = log[x]            
        versions.append(
            dict(version_id=len(log)-x-1,
                 author=version['fields']['properties']['opencore.author'],
                 modification_date=version['fields']['properties']['opencore.timestamp'],
                 comment=version['fields']['message']))
    return versions

from DateTime import DateTime
def import_repo(portal, project_path):
    cat = portal.portal_catalog
    pr = portal.portal_repository
    pages = cat(path="/openplans/projects/%s/" % project_path, portal_type="Document")
    changes = []
    for page in pages:
        history = pr.getHistory(page.getObject())
        for version in history:
            changes.append((DateTime(version.sys_metadata['timestamp']), version))

    changes = sorted(changes)
    repo = BzrAccess("/tmp/opencorebzr/%s/" % project_path)
    for change in changes:
        time, change = change[0], change[1]
        repo.write(change.object.getId(),
                   change.object.EditableBody(),
                   msg=change.comment,
                   revprops={'opencore.author': change.sys_metadata['principal'],
                             'opencore.timestamp': str(change.sys_metadata['timestamp']),
                             })
