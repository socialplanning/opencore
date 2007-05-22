from Products.CMFCore.utils import getToolByName
from cStringIO import StringIO

def find_duplicate_emails(self):
    out = StringIO()
    mb = getToolByName(self, 'membrane_tool')
    brains = mb(getEmail='')
    all_emails = [x.getEmail for x in brains]
    unique_emails = set()
    duplicate_emails = []
    for email in all_emails:
        if not email: continue
        if email in unique_emails:
            if email not in duplicate_emails:
                duplicate_emails.append(email)
        else:
            unique_emails.add(email)
    for email in duplicate_emails:
	if not email: continue
        brains = mb(getEmail=email)
        out.write('%s\n' % email)
        for brain in brains:
            try:
                mem = brain.getObject()
            except AttributeError:
                continue
            id = mem.getId()
            login_time = mem.login_time
            projects = mem.getProjectListing()
	    projects = [x.Title() for x in projects]
	    if projects:
                out.write('    %s - Login Time: %s, Projects: %s\n' % (id, login_time, ', '.join(projects)))
            else:
                out.write('    %s - Login Time: %s\n' % (id, login_time))
        out.write('\n')
    return out.getvalue()
