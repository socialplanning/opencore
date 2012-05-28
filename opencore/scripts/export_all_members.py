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

def getMembersCSV(self, outfile):

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
        row.append("<PORTRAIT_URL>")
        row.append("<SITE_ROLE>")
        row.append(MemberWorkflowHandler(member).is_unconfirmed() and "unconfirmed" or "confirmed")
        
        writer.writerow(row)


import sys
outfile = "/tmp/members.csv"
outfile = open(outfile, 'w')
try:
    getMembersCSV(app.openplans, outfile)
finally:
    outfile.close()
