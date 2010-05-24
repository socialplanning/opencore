"""
A `zopectl run` script that makes message mbox and subscriber csv
exports of ALL mailing lists.  Mostly just for testing.
"""
from Products.listen.extras import import_export
from Testing.makerequest import makerequest
from AccessControl.SecurityManagement import newSecurityManager
from zope.app.component.hooks import setSite

app = makerequest(app)
setSite(app.openplans)
admin = app.acl_users.getUser('admin').__of__(app.acl_users)
newSecurityManager(None, admin)

for proj in app.openplans.projects.objectValues(['OpenProject']):
    try:
        listfol = proj['lists']
    except KeyError:
        continue
    lists = listfol.objectValues(['OpenMailingList'])
    for list_ in lists:
        print "Exporting %s..." % list_.getId()
        exporter = import_export.MailingListMessageExporter(list_)
        mbox = exporter.export_messages()
        exporter = import_export.MailingListSubscriberExporter(list_)
        subs = exporter.export_subscribers()
        print "exported %s OK" % list_.getId()
        fname = '_'.join(list_.getPhysicalPath()).strip('_')
        open('/tmp/list_exports/%s.mbox' % fname, 'w').write(mbox)
        open('/tmp/list_exports/%s.csv' % fname, 'w').write(subs)


