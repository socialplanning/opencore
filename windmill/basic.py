from lib.user import create_user
from lib.user import create_user_duplicate
from lib.user import delete_user
from lib.utils import logout
from suite import Suite

class BasicSuite(Suite):
    """
    OpenPlans basic functional test suite. 
    """
    name = 'Basic'
    
    def _run(self):
        client = self.client
        self.create_user_with_errors()
        create_user(client)
        logout(client)
        create_user_duplicate(client)    

    def cleanup(self):
        delete_user()

    def create_user_with_errors(self):
        client = self.client
        client.click(link=u'Create account')
        client.waits.forPageLoad()
        client.type(text=u'test_error 123$!@$#%!#@$%', id=u'id')
        client.type(text=u'test name 12345%@!#$', id=u'fullname')
        client.type(text=u'bad email address', id=u'email')
        client.type(text=u'a', id=u'password')
        client.type(text=u'a', id=u'confirm_password')
        client.click(name=u'task|join')
        client.waits.forPageLoad()
        client.asserts.assertNode(id=u'oc-id-error')
        client.asserts.assertText(validator=u'The login name you selected is not valid. Usernames must start with a letter and consist only of letters, numbers, and underscores.  Please choose another.', id=u'oc-id-error')
        client.asserts.assertNode(xpath=u'/html/body/div/div/div/div/div/form/fieldset/table/tbody/tr[2]/td[2]/span')
        client.asserts.assertText(xpath=u'/html/body/div/div/div/div/div/form/fieldset/table/tbody/tr[2]/td[2]/span', validator=u'                      (optional)\n                    ')
        client.asserts.assertNode(id=u'oc-email-error')
        client.asserts.assertText(validator=u'That email address is invalid.', id=u'oc-email-error')
        client.asserts.assertNode(id=u'oc-password-error')
        client.asserts.assertText(validator=u'Passwords must contain at least 5 characters.', id=u'oc-password-error')
        client.type(text=u'abcdef', id=u'password')
        client.type(text=u'bcdefg', id=u'confirm_password')
        client.click(name=u'task|join')
        client.waits.forPageLoad()
        client.asserts.assertText(validator=u'Passwords do not match.', id=u'oc-password-error')
        # password fields should have been cleared out
        client.click(name=u'task|join')
        client.waits.forPageLoad()
        client.asserts.assertNode(id=u'oc-password-error')
        client.asserts.assertText(validator=u'Please enter a password', id=u'oc-password-error')
