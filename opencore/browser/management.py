from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.Five.formlib import formbase
from Products.OpenPlans.Extensions.create_test_content import create_test_content
from cStringIO import StringIO
from interfaces import IAddOpenPlans
from zope.formlib import form

from opencore.browser.base import BaseView
from opencore.member.workflow import MemberWorkflowHandler
from zipfile import ZipFile
from DateTime import DateTime

import transaction

class ModerateUsers(BaseView):

    def get_users(self):
        brains = self.membranetool(sort_on='created',
                                   sort_order='descending',
                                   sort_limit=500)
        return brains

    def NO_TIME(self):
        return DateTime('2000/01/01')

class ImportUsers(BaseView):

    def __call__(self, *args, **kwargs):
        import csv, sys, os
        fp = open(self.request.form.get("file"))
        data = csv.reader(fp)

        portraits_dir = self.request.form.get("portraits")

        joinview = self.context.restrictedTraverse("@@join")
        membertool = getToolByName(self.context, "portal_membership")

        header = data.next()
        i = 0
        j = 0
        for member in data:
            member = dict(zip(header, member))

            print i, j, member['member_id']

            j += 1
            self.request.form.clear()
            self.request.form.update({"id": member['member_id'],
                                      "email": member['email'],
                                      "password": "changeme",
                                      "fullname": member['fullname'],
                                      "confirm_password": "changeme",
                                      "skip_case_insensitive_username_check": 1,
                                      "skip_email_check": 1,
                                      })
            mem_obj = joinview._create_member(confirmed=True) # This doesn't confirm the user; it just suppresses email notification.
            if isinstance(mem_obj, dict):
                if mem_obj == {'id': u'The login name you selected is already in use. Please choose another.'}:
                    continue
                print mem_obj
                continue
            if member['is_confirmed'] == "confirmed":
                MemberWorkflowHandler(mem_obj).confirm()
                membertool.createMemberArea(member['member_id'])

            mem_obj.getField("password").set(mem_obj, member['password'])
            
            mem_obj.getField("creation_date").set(mem_obj, 
                                                  DateTime(member['creation_date']))
            
            
            if 'last_login_date' in member:
                mem_obj.setLogin_time(DateTime(member['last_login_date']))

            for field in "location home_page description statement skills affiliations website background favorites".split():
                mem_obj.getField(field).set(mem_obj, member[field])

            portrait = member['portrait']
            if portrait:
                portrait = open(os.path.join(portraits_dir, portrait), 'rb')
                mem_obj.setPortrait(portrait)
                portrait = mem_obj.getPortrait()
                portrait.filename = member['portrait_filename']
                portrait.getField("creation_date").set(
                    portrait, DateTime(member['portrait_created_on']))
                portrait.getField("modification_date").set(
                    portrait, DateTime(member['portrait_modified_on']))
                portrait.Schema()['creators'].set(portrait, (member['portrait_creator'],))
                portrait.creators = (member['portrait_creator'],) 

            if member['site_role'] == "admin":
                self.context.manage_setLocalRoles(member['member_id'], ("Manager",))

            mem_obj.reindexObject()

            i += 1
            if i % 500 == 0:
                transaction.commit()
        transaction.commit()
        return "ok"

class TestContentCreator(formbase.PageForm):
    label = 'Create Dummy Projects and Members'
    form_fields = form.Fields()

    @form.action('Create')
    def handle_create_action(self, action, data):
        self.status = create_test_content(self.context)


class AddOpenPlansForm(formbase.AddForm):
    form_fields = form.Fields(IAddOpenPlans)
    profiles = ('opencore.configuration:default',)

    @property
    def factory(self):
        return self.context.manage_addProduct['CMFPlone'].addPloneSite

    def createAndAdd(self, data):
        self.status='Creating Site\n'
        self.factory(data['id'],
                     data['title'],
                     extension_ids=self.profiles)

        portal = getattr(self.context, data['id'])
        if data.get('testcontent'):
            self.status = self.status + create_test_content(portal)

        self.request.response.redirect(portal.absolute_url())

