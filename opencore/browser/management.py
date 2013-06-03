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

from DateTime import DateTime

class ImportUsers(BaseView):

    def __call__(self, *args, **kwargs):
        import csv, sys, os
        fp = open(self.request.form.get("file"))
        data = csv.reader(fp)
        joinview = self.context.restrictedTraverse("@@join")
        membertool = getToolByName(self.context, "portal_membership")

        header = data.next()
        for member in data:
            member = dict(zip(header, member))
            if "jucovy" not in member['email'] and member['member_id'] != "ejucovy":
                continue

            self.request.form.clear()
            self.request.form.update({"id": member['member_id'],
                                      "email": member['email'],
                                      "password": "changeme",
                                      "fullname": member['fullname'],
                                      "confirm_password": "changeme",
                                      })
            mem_obj = joinview._create_member(confirmed=True) # This doesn't confirm the user; it just suppresses email notification.
            if isinstance(mem_obj, dict):
                print mem_obj
                continue
            if member['is_confirmed'] == "confirmed":
                MemberWorkflowHandler(mem_obj).confirm()
                membertool.createMemberArea(member['member_id'])

            mem_obj.getField("password").set(mem_obj, member['password'])
            
            mem_obj.getField("creation_date").set(mem_obj, 
                                                  DateTime(member['creation_date']))
            for field in "location home_page description statement skills affiliations website background favorites".split():
                mem_obj.getField(field).set(mem_obj, member[field])
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

