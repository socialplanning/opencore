# Based on http://blog.kagesenshi.org/2008/05/exporting-plone30-memberdata-and.html

# Memberdata export script for Plone 3.0
#
# based on:
#    http://transcyberia.info/archives/23-howto-sync-mailman-from-plone.html
#    http://www.zopelabs.com/cookbook/1140753093
#    http://plone.org/documentation/how-to/export-member-data-to-csv
#
# desc:
#    None of the scripts above can extract password hashes on Plone3.0, 
#    BUT THIS ONE CAN!!!
#
#    Execute this as normal External Script, and DON'T make it public accessible 
#    (unless you don't mind people having your hashes). You have been warned. 
#    Have fun (^,^)
#

from opencore.utils import setup
app = setup(app)

from StringIO import StringIO
import csv
import time

from opencore.member.workflow import MemberWorkflowHandler
import os
import mimetypes

def getMembersCSV(self, outfile, portrait_dir):

    writer = csv.writer(outfile)

    # core properties (username/password)
    core_properties = ['member_id','password']

    # extra portal_memberdata properties
    extra_properties = ['fullname',
                        'email',
                        'location',
                        'home_page',
                        'description',
                        'statement',
                        'skills',
                        'affiliations',
                        'website',
                        'background',
                        'favorites']

    also =             ['portrait',
                        'site_role',
                        'is_confirmed',
                        ]

    properties = core_properties + extra_properties + also

    writer.writerow(properties)

    membership = self.portal_membership

    for memberId in membership.listMemberIds():
        row = []
        member = membership.getMemberById(memberId)
        for property in core_properties + extra_properties:
            if property == 'member_id':
               row.append(memberId)
            elif property == 'password':
               row.append(member.password)
            else:
               row.append(member.getProperty(property))
        portrait_url = ""
        portrait = member.getPortrait()
        if portrait:
            extension = mimetypes.guess_extension(portrait.content_type) or ''
            portrait_url = "%s%s" % (memberId, extension)
            portrait_url = os.path.join(portrait_dir, portrait_url)
            portrait_file = open(portrait_url, 'w')

            ## Usually portrait.data is the raw bytes of the file
            #  but sometimes it's one of these OFS Pdata guys
            if isinstance(portrait.data, basestring):
                portrait_file.write(portrait.data)
            else:
                assert isinstance(portrait.data.data, basestring)
                portrait_file.write(portrait.data.data)
            portrait_file.close()
        row.append(portrait_url)
        row.append("<SITE_ROLE>")
        row.append(MemberWorkflowHandler(member).is_unconfirmed() and "unconfirmed" or "confirmed")
        
        writer.writerow(row)


import tempfile
import sys

fd, outfile = tempfile.mkstemp(prefix="opencore-members", suffix=".csv")
outfp = open(outfile, 'w')

outdir = tempfile.mkdtemp(prefix="opencore-member-portraits")

print outfile, outdir

try:
    getMembersCSV(app.openplans, outfp, outdir)
finally:
    outfp.close()

#os.unlink(outfile)
#shutil.rmtree(outdir)
