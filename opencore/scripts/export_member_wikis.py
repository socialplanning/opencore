from opencore.utils import setup

#app = setup(app)

#mem = sys.argv[-1]

#mfolder = app.openplans.people[mem]

vardir = "/opt/backup.openfsm.net/var/backup/member_exports/"

from opencore.interfaces.message import ITransientMessage
import simplejson as json

def export_one_member(folder, namespace, archive_prefix):

    import tempfile, os, shutil

    outdir = os.path.join(vardir, folder.getId())
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    tempdir = tempfile.mkdtemp()
    tmpdbdir = os.path.join(tempdir, "tmpdbs")
    repodir = os.path.join(tempdir, "bzr_repos")
    checkoutdir = os.path.join(tempdir, "bzr_checkouts")
    
    from opencore.nui.wiki import bzrbackend
    converter = bzrbackend.WikiConverter(folder, tmpdbdir, repodir, checkoutdir, namespace=namespace)

    clonedir, filename_map = converter.convert()
    root_len = len(os.path.abspath(clonedir))
    
    import zipfile
    TEMP_PREFIX='temp_member_export'
    tmpfd, tmpname = tempfile.mkstemp(suffix='.zip', prefix=TEMP_PREFIX, dir=outdir)
    tmp = os.fdopen(tmpfd, 'w')   # Dunno why mkstemp returns a file descr.
    zfile = zipfile.ZipFile(tmp, 'w')
    
    for root, dirs, files in os.walk(clonedir):
        relative_root = os.path.abspath(root)[root_len:].strip(os.sep)
        archive_root = os.path.join(archive_prefix,
                                    'wiki_history',
                                    relative_root)
        for f in files:
            fullpath = os.path.join(root, f)
            archive_name = os.path.join(archive_root, f)
            zfile.write(fullpath, archive_name)
    zfile.writestr(os.path.join(archive_prefix,
                                "wiki_history_filenames.json"),
                   json.dumps(filename_map))
    if namespace == "people":

        file_metadata = {}
        for afile in folder.portal_catalog(
            portal_type=("FileAttachment", "Image"), path='/'.join(folder.getPhysicalPath())):

            obj = afile.getObject()
            relative_path = afile.getPath()[len('/'.join(folder.getPhysicalPath())):].lstrip('/')
            out_path = "%s/pages/%s" % (archive_prefix, relative_path)

            metadata = {
                'creator': obj.Creator(),
                'creation_date': str(obj.creation_date),
                'title': obj.Title(),
                }
            file_metadata[out_path] = metadata

            if isinstance(obj.data, basestring):
                zfile.writestr(out_path, str(obj))
                continue
            data = obj.data
            import tempfile
            temp = tempfile.NamedTemporaryFile(delete=True)
            try:
                while data is not None:
                    temp.write(data)
                    data = data.next
                zfile.write(temp.name, out_path)
            finally:
                temp.close()
        zfile.writestr("%s/attachments.json" % archive_prefix, 
                              json.dumps(file_metadata))


        _msgs = ITransientMessage(folder.openplans).get_all_msgs(folder.getId())
        msgs = {}
        for category in _msgs:
            msgs[category] = []
            keys = sorted(_msgs[category].keys())
            for key in keys:
                msgs[category].append(_msgs[category][key])

        zfile.writestr(os.path.join(archive_prefix, 'notifications.json'),
                       json.dumps(
                msgs))
        
    zfile.close()
    return tmpname

if __name__ == '__main__':
    import sys
    from opencore.utils import setup
    app = setup(app)
    print export_one_member(app.openplans.people[sys.argv[1]], "people", sys.argv[1])
    #export_one_member(app.openplans.news, "news", "news")
