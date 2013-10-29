from opencore.utils import setup

app = setup(app)

mem = sys.argv[-1]

def export_one_member(mem):

    mfolder = app.openplans.people[mem]

    import tempfile, os, shutil

    tempdir = tempfile.mkdtemp()
    tmpdbdir = os.path.join(tempdir, "tmpdbs")
    repodir = os.path.join(tempdir, "bzr_repos")
    checkoutdir = os.path.join(tempdir, "bzr_checkouts")
    
    from opencore.nui.wiki import bzrbackend
    converter = bzrbackend.WikiConverter(mfolder, tmpdbdir, repodir, checkoutdir, namespace="people")

    clonedir, filename_map = converter.convert()
    root_len = len(os.path.abspath(clonedir))
    
    import zipfile
    TEMP_PREFIX='temp_member_export'
    tmpfd, tmpname = tempfile.mkstemp(suffix='.zip', prefix=TEMP_PREFIX)
    tmp = os.fdopen(tmpfd, 'w')   # Dunno why mkstemp returns a file descr.
    zfile = zipfile.ZipFile(tmp, 'w')
    
    for root, dirs, files in os.walk(clonedir):
        relative_root = os.path.abspath(root)[root_len:].strip(os.sep)
        archive_root = os.path.join('people', mem,
                                    'wiki_history',
                                    relative_root)
        for f in files:
            fullpath = os.path.join(root, f)
            archive_name = os.path.join(archive_root, f)
            zfile.write(fullpath, archive_name)
            
    zfile.close()
    print tmpname
