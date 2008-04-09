from opencore.browser.base import BaseView
import os

class ExportView(BaseView):
    """
    A really dumb script to export a project's wiki pages as html.

    Not hooked in anywhere via ZCML, because it is so dumb.  Some caveats:
     * Note that it creates and removes files and directories on the server's filesystem
       using untrusted data (ie project name, page title, etc). This is ***very very bad***
       and could potentially result in catastrophic data loss. Like if a page was titled
       "../{etc}"
     * It uses /home/egj/ everywhere. This is intentional, to remind you
       that it isn't hooked in and that you should not use it, because it is horribly
       unsafe (see above)
     * It doesn't actually return the zip file to the user. It just sticks it on the fs for
       an admin to deal with.
     * It doesn't rewrite links or include attachments or referenced images, so all links
       will be broken. ianbicking has probably written a clever script to address this.
     * It only exports current versions of wiki pages; no other site content is exported.
    """
    def export(self):
        pc = self.get_tool("portal_catalog")
        pages = pc(portal_type="Document", path=self.context.absolute_url_path())
        project_id = self.context.getId()
        from zipfile import ZipFile
        z = ZipFile("/home/egj/%s.zip" % self.context.getId(), 'w')
        dirpath = "/home/egj/%s" % project_id
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        for page in pages:
            try:
                page = page.getObject()
            except AttributeError:
                # sometimes the catalog references a dead object.
                # we'll fail silently for lack of a better idea.
                continue
            text = page.getText()
            title = page.getId()
            
            fp = open("%s/%s.html" % (dirpath, title), 'w')
            fp.write(text)
            fp.close()
            z.write("%s/%s.html" % (dirpath, title))
            os.remove("%s/%s.html" % (dirpath, title))
        z.close()
        os.rmdir(dirpath)
        return "Great!  Now ask a site administrator to email you the file."
