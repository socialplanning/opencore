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

    if namespace == "people":
        zfile.writestr(os.path.join(archive_prefix, 'notifications.json'),
                       json.dumps(
                ITransientMessage(folder.openplans).get_all_msgs(folder.getId())))
        
    zfile.close()
    return tmpname

#export_one_member(mfolder, "people", "people/%s" % mem)
#import pdb; pdb.set_trace()
#export_one_member(app.openplans.news, "news", "news")
