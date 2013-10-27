from opencore.utils import setup
import transaction
from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
import sys
from zipfile import ZipFile
from zope.app.component.hooks import setSite

def main(app, zipfile, project):
    user = app.acl_users.getUser('admin')
    print "Changing stuff as user", user
    newSecurityManager(None, user)
    app = makerequest(app)

    project = app.openplans.projects[project]
    proj_id = project.getId()

    zipfile = open(zipfile, 'rb')
    zipfile = ZipFile(zipfile)

    settings = [zipfile.read(i) for i in zipfile.namelist() 
                if i
                and len(i.split("/")) == 4 
                and i.split("/")[1] == "lists" 
                and i.split("/")[3] == "settings.ini"]
    
    from libopencore.import_utils import parse_listen_settings
    settings = [parse_listen_settings(i) for i in settings]

    from opencore.listen.mailinglist import OpenMailingList
    lists_folder = project.lists.aq_inner
    imported_ids = []
    for list in settings:
        print "Creating list %s in project %s" % (list['info']['id'], proj_id)
        request = project.REQUEST
        request.set('title', list['info']['title'])
        lists_folder.invokeFactory(OpenMailingList.portal_type, 
                                   list['info']['id'])
        ml = lists_folder[list['info']['id']]
        ml.mailto = list['info']['mailto'].split("@")[0]
        ml.managers = tuple(list['managers'])
        ml.setDescription(list['description'])
        
        workflow = list['preferences']['list_type']

        from opencore.listen.utils import workflow_to_mlist_type
        old_workflow_type = ml.list_type
        new_workflow_type = workflow_to_mlist_type(workflow)
        from zope.event import notify
        from Products.listen.content import ListTypeChanged
        notify(ListTypeChanged(ml, old_workflow_type.list_marker, new_workflow_type.list_marker))
        
        archive = list['preferences']['archive_setting']
        
        archive = ['with_attachments', 'plain_text', 'not_archived'].index(archive)
        ml.archived = archive
        
        try:
            private_archives = list['preferences']['private_archives']
            ml.private_archives = private_archives
        except:
            pass

        if list['preferences']['sync_membership']:
            from zope.interface import alsoProvides
            from opencore.listen.interfaces import ISyncWithProjectMembership
            alsoProvides(ml, ISyncWithProjectMembership)

        ml.creators = (list['info']['created_by'], )
        ml.getField("creation_date").set(ml, list['info']['created_on'])
        ml.getField("modification_date").set(ml, list['info']['modified_on'])

        imported_ids.append(ml.getId())

    transaction.get().commit(True)

    from StringIO import StringIO

    print "Creating archives"

    archives = [i for i in zipfile.namelist() 
                if i
                and len(i.split("/")) == 4 
                and i.split("/")[1] == "lists" 
                and i.split("/")[3] == "archive.mbox"]
    
    for ml_id in imported_ids:
        archive = [i for i in archives if i.split("/", 1)[1] == "lists/%s/archive.mbox" % ml_id]
        if not archive: continue
        archive = archive[0]

        print "Importing archive for list %s" % ml_id

        archive = zipfile.read(archive)
        archive = StringIO(archive)
        
        from Products.listen.extras.import_export import (
            MailingListMessageImporter,
            MailingListSubscriberImporter)
        ml = project.lists[ml_id]
        setSite(ml)

        importer = MailingListMessageImporter(ml)
        importer.import_messages(archive)

    memberlists = [i for i in zipfile.namelist() 
                   if i
                   and len(i.split("/")) == 4 
                   and i.split("/")[1] == "lists" 
                   and i.split("/")[3] == "subscribers.csv"]

    print "Importing subscribers"

    transaction.get().commit(True)

    setSite(app.openplans)
    for ml_id in imported_ids:
        memberlist = [i for i in memberlists
                      if i.split("/", 1)[1] == "lists/%s/subscribers.csv" % ml_id]
        if not memberlist: continue
        memberlist = memberlist[0]

        memberlist = zipfile.read(memberlist)
        memberlist = StringIO(memberlist)
        members = [s.strip().split(",")[-2:] for s in memberlist]
        members = [e for e in members if '@' in e[0]
                   and e[1].strip() in ("subscribed", "allowed")]
        
        
        ml = project.lists[ml_id]
        
        from Products.listen.extras.import_export import \
            MailingListSubscriberImporter
        importer = MailingListSubscriberImporter(ml)
        importer.import_subscribers(members)

    setSite(app.openplans)

    #importer = MailingListSubscriberImporter(ml)
    #subscribers = zipfile.read("%s/lists/%s/subscribers.csv" % (
    #            proj_id, ml_id))
    #subscribers 
    #importer.import_subscribers(subscribers)

