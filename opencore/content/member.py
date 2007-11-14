import sys
import random
import re
from types import TupleType, ListType, UnicodeType

from AccessControl import ClassSecurityInfo

from zope.component import getAdapter
from zope.component import getUtility

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCorePermissions import *
import Products.Archetypes.public as atapi
from Products.Archetypes.ExtensibleMetadata import ExtensibleMetadata
from Products.Archetypes.ArchetypeTool import base_factory_type_information as bfti
from Products.Archetypes.Field import STRING_TYPES
from Products.Archetypes.public import Schema, StringField, StringWidget
from Products.validation.validators.BaseValidators import EMAIL_RE

from Products.membrane.config import TOOLNAME as MBTOOLNAME
from Products.remember.content.member_schema \
     import id_schema, contact_schema, plone_schema, \
     security_schema, login_info_schema
from Products.remember.content.member import FolderishMember
from Products.remember.interfaces import IHashPW
from Products.remember.config import ALLOWED_MEMBER_ID_PATTERN

from Products.OpenPlans.config import PROJECTNAME
from Products.OpenPlans.config import PROHIBITED_MEMBER_PREFIXES

from opencore.utility.interfaces import IHTTPClient

member_schema = id_schema + contact_schema + plone_schema + \
                security_schema + login_info_schema
content_schema = member_schema.copy() # copy before editing

# specify which fields are searchable in the roster
content_schema['id'].rosterSearch = 1
content_schema['fullname'].rosterSearch = 1
content_schema['location'].rosterSearch = 1
content_schema['location'].index = \
  ('membrane_tool/ZCTextIndex,lexicon_id=member_lexicon,index_type=Cosine Measure|TextIndex:brains',)

content_schema['title'].write_permission = 'Manage users'
content_schema['title'].widget.visible= {'view': 'invisible'}

content_schema['wysiwyg_editor'].default = 'Kupu'
content_schema['wysiwyg_editor'].write_permission = 'Manage site'
content_schema['wysiwyg_editor'].widget.visible = {'edit':'invisible',
                                                   'view':'invisible'}
content_schema['login_time'].mode = 'rw'
content_schema['login_time'].mutator = 'setLoginTime'

content_schema['visible_ids'].default = False

content_schema['email'].read_permission = ModifyPortalContent

content_schema['mail_me'].regfield = 0

content_schema['make_private'].widget.visible = {'edit': 'invisible'}

content_schema['portrait'].sizes=dict(thumb=(80,80),
                                      icon=(32,32)
                                      )
content_schema['portrait'].max_size=(200,200)

# new fields for nui profile
nuischema = Schema((
                    StringField(
                      'statement',
                      index='ZCTextIndex,lexicon_id=plone_lexicon,index_type=Cosine Measure|TextIndex:brains',
                      searchable=1,
                      widget=StringWidget(
                        label='Statement',
                        label_msgid='label_statement',
                        description_msgid='desc_statement',
                        description='statement description.',
                        size=50,
                        ),
                      ),
                    StringField(
                      'skills',
                      index='ZCTextIndex,lexicon_id=plone_lexicon,index_type=Cosine Measure|TextIndex:brains',
                      searchable=1,
                      widget=StringWidget(
                        label='skills',
                        label_msgid='label_skills',
                        description_msgid='desc_skills',
                        description='skills description.',
                        size=50,
                        ),
                      ),
                    StringField(
                      'affiliations',
                      index='ZCTextIndex,lexicon_id=plone_lexicon,index_type=Cosine Measure|TextIndex:brains',
                      searchable=1,
                      widget=StringWidget(
                        label='affiliations',
                        label_msgid='label_affiliations',
                        description_msgid='desc_affiliations',
                        description='affiliations description.',
                        size=50,
                        ),
                      ),
                    StringField(
                      'website',
                      searchable=1,
                      widget=StringWidget(
                        label='website',
                        label_msgid='label_website',
                        description_msgid='desc_website',
                        description='website description.',
                        size=50,
                        ),
                      ),
                    StringField(
                      'background',
                      index='ZCTextIndex,lexicon_id=plone_lexicon,index_type=Cosine Measure|TextIndex:brains',
                      searchable=1,
                      widget=StringWidget(
                        label='background',
                        label_msgid='label_background',
                        description_msgid='desc_background',
                        description='background description.',
                        size=50,
                        ),
                      ),
                    StringField(
                      'favorites',
                      index='ZCTextIndex,lexicon_id=plone_lexicon,index_type=Cosine Measure|TextIndex:brains',
                      searchable=1,
                      widget=StringWidget(
                        label='favorites',
                        label_msgid='label_favorites',
                        description_msgid='desc_favorites',
                        description='favorites description.',
                        size=50,
                        ),
                      ),
                    ))

content_schema += nuischema


content_schema += atapi.Schema((
    atapi.BooleanField('useAnonByDefault',
                       mode='rw',
                       default=True,
                       read_permission=ModifyPortalContent,
                       write_permission=ModifyPortalContent,
                       widget=atapi.BooleanWidget(
                           label='Anonymize email address by default?',
                           label_msgid='label_useAnonByDefault',
                           description="Would you like your email address to be anonymized by " \
                                       "default when sending email via the forms on this site?",
                           description_msgid='help_useAnonByDefault',
                           ),
                       ),

    atapi.ComputedField('projects',
                        read_permission=View,
                        expression='context.getProjectListing()',
                        widget=atapi.ComputedWidget(
                            label="Projects",
                            label_msgid='label_projects',
                            description="Projects this user is a member of.",
                            description_msgid='help_projects',
                            macro='member_projects',
                            ),
                        ),
    ))

content_schema.moveField('useAnonByDefault', after='email')

actions = bfti[0].copy()['actions']
for action in actions:
    if action['id'] == 'metadata':
        action['permissions'] = ('Manage users',)

class OpenMember(FolderishMember):
    """ OpenPlans Member Object """
    security = ClassSecurityInfo()
    portal_type = meta_type = 'OpenMember'
    archetype_name = 'OpenPlans Member'   #this name appears in the 'add' box

    schema = content_schema + ExtensibleMetadata.schema

    # uncomment lines below when you need
    factory_type_information={
        #'content_icon':'PDB.gif',
        'immediate_view':'base_view',
        #'global_allow':1,
        'filter_content_types':1,
        }

    actions = actions    

    security.declareProtected(ManagePortal, 'getUserConfirmationCode')
    def getUserConfirmationCode(self):
        """
        Return the user's unique confirmation code to complete
        registration manually
        """
        return '%sconfirm%s' % (self.UID(), self._confirmation_key)

    security.declareProtected(ManagePortal, 'setUserConfirmationCode')
    def setUserConfirmationCode(self):
        self._confirmation_key = '%x' % random.randint(0, sys.maxint)

    security.declareProtected(View, 'getActiveTeams')
    def getActiveTeams(self):
        """
        Returns a list of teams on which the member is active.
        """
        tmtool = getToolByName(self, 'portal_teams')
        return tmtool.getTeamsByMemberId(self.getId(), active=True)

    security.declareProtected(View, 'getProjectListing')
    def getProjectListing(self):
        mtool = getToolByName(self, 'portal_membership')
        projects = {}
        for team in self.getActiveTeams():
            for space in team.getTeamSpaces():
                if mtool.checkPermission(View, space):
                    projects[space] = None
        return projects.keys()            

    # XXX is this used?
    security.declareProtected(View, 'projectBrains')
    def projectBrains(self):
        catalog = getToolByName(self, 'portal_catalog')
        teamtool = getToolByName(self, 'portal_teams')
        mships = catalog(id=self.getId(), portal_type='OpenMembership',
                         review_state=teamtool.getDefaultActiveStates())
        teams = [i.getPath().split('/')[-2] for i in mships]
        projects = catalog(portal_type='OpenProject', id=teams)
        return projects

    security.declareProtected(View, 'RosterSearchableText')
    def RosterSearchableText(self):
        ### abstract to a config or top of file
        return self.getTextForFilteredFields(rosterSearch=1)
    
    def getTextForFilteredFields(self, *args, **kw):
        """
        Utility method for multiple field indexes 
        ganked from Archetypes.BaseObject.SearchableText. takes a
        method or kw s (and passes them on to filterFields())
        """
        data = []
        charset = self.getCharset()
        fields = self.Schema().filterFields(*args, **kw)
        for field in fields:
            method = field.getAccessor(self)
            try:
                datum =  method(mimetype="text/plain")
            except TypeError:
                # retry in case typeerror was raised because accessor doesn't
                # handle the mimetype argument
                try:
                    datum =  method()
                except:
                    continue

            if datum:
                type_datum = type(datum)
                vocab = field.Vocabulary(self)
                if type_datum is ListType or type_datum is TupleType:
                    # Unmangle vocabulary: we index key AND value
                    vocab_values = map(lambda value, vocab=vocab: vocab.getValue(value, ''), datum)
                    datum = list(datum)
                    datum.extend(vocab_values)
                    datum = ' '.join(datum)
                elif type_datum in STRING_TYPES:
                    datum = "%s %s" % (datum, vocab.getValue(datum, ''), )

                # FIXME: we really need an unicode policy !
                if type_datum is UnicodeType:
                    datum = datum.encode(charset)
                    
                data.append(str(datum))

        data = ' '.join(data)
        return data

    security.declarePrivate('_remote_auth_sites')
    def _remote_auth_sites(self):
        ptool = getToolByName(self, 'portal_properties')
        ocprops = ptool._getOb('opencore_properties')
        remote_auth_sites = ocprops.getProperty('remote_auth_sites')
        remote_auth_sites = [s for s in remote_auth_sites if s.strip()]
        return remote_auth_sites

    security.declarePrivate('_id_exists_remotely')
    def _id_exists_remotely(self, id):
        """
        Checks all of the servers in the remote_auth_sites property to
        see if this specified id exists on any of those sites.
        """
        remote_auth_sites = self._remote_auth_sites()
        if remote_auth_sites:
            http = getUtility(IHTTPClient)
            for url in remote_auth_sites:
                mem_url = "%s/%s/exists" % (url, member_path(id))
                resp, content = http.request(mem_url)
                if resp.status == 200:
                    # a remote member exists
                    return True
        return False

    security.declarePrivate('validate_id')
    def validate_id(self, id):
        """
        Override the default id validation to disallow ids that vary
        from existing ids only by case.
        """
        # we can't always trust the id argument, b/c the autogen'd
        # id will be passed in if the reg form id field is blank
        form = self.REQUEST.form
        if form.has_key('id') and not form['id']:
            return self.translate('Input is required but no input given.',
                                  default='You did not enter a login name.')
        elif self.getId() and id != self.getId():
            # we only validate if we're changing the id
            allowed = True
            mbtool = getToolByName(self, 'membrane_tool')
            if len(mbtool.unrestrictedSearchResults(getUserName=id)) > 0 or \
                   not ALLOWED_MEMBER_ID_PATTERN.match(id):
                allowed = False
            if allowed:
                for prefix in PROHIBITED_MEMBER_PREFIXES:
                    if id.lower().startswith(prefix):
                        allowed = False
            if allowed and self._id_exists_remotely(id):
                allowed = False
            if not allowed:
                msg = "The login name you selected is already " + \
                      "in use or is not valid. Please choose another."
                return self.translate(msg, default=msg)

    security.declarePrivate('_id_exists_remotely')
    def _email_exists_remotely(self, email):
        """
        Checks all of the servers in the remote_auth_sites property to
        see if this specified id exists on any of those sites.
        """
        remote_auth_sites = self._remote_auth_sites()
        if remote_auth_sites:
            http = getUtility(IHTTPClient)
            for url in remote_auth_sites:
                email_url = "%s/people/email?email=%s" % (url, email)
                resp, content = http.request(email_url, method='HEAD')
                if resp.status == 200:
                    return True
        return False

    security.declarePrivate('validate_email')
    def validate_email(self, email):
        """
        Force email addresses to be unique throughout the system.
        """
        form = self.REQUEST.form
        if form.has_key('email') and not form['email']:
            return self.translate('Input is required but no input given.',
                                  default='You did not enter an email address.')
        regex = re.compile(EMAIL_RE)
        if regex.match(email) is None:
            msg = "That email address is invalid."
            return self.translate(msg, default=msg)
        if email != self.getEmail():
            mbtool = getToolByName(self, 'membrane_tool')
            if len(mbtool.unrestrictedSearchResults(getEmail=email)) > 0 \
                   or self._email_exists_remotely(email):
                msg = ("That email address is already in use.  "
                       "Please choose another.")
                return self.translate(msg, default=msg)

    def __bobo_traverse__(self, REQUEST, name):
        """Transparent access to image scales
           **adapted from ATCT**
        """
        if name.startswith('portrait'):
            field = self.getField('portrait')
            image = None
            if name == 'portrait':
                image = field.getScale(self)
            else:
                scalename = name[len('portrait_'):]
                if scalename in field.getAvailableSizes(self):
                    image = field.getScale(self, scale=scalename)
            if image is not None and not isinstance(image, basestring):
                # image might be None or '' for empty images
                return image

        return FolderishMember.__bobo_traverse__(self, REQUEST, name)

    def verifyCredentials(self, credentials):
        """
        We override base member class's verifyCredentials for two reasons:

        o to be able to support case insensitive login.

        o to mark the credentials object to negate a check by the remote
          auth plug-in
        """
        mbtool = getToolByName(self, MBTOOLNAME)
        login = credentials.get('login')
        if not mbtool.case_sensitive_auth:
            login = login.lower()
        password = credentials.get('password')
        try:
            hash_type, hashed = self.getPassword().split(':', 1)
        except ValueError:
            raise ValueError('Error parsing hash type. '
                             'Please run migration')
        hasher = getAdapter(self, IHashPW, hash_type)
        username = self.getUserName()
        if not mbtool.case_sensitive_auth:
            username = username.lower()
        if login == username:
            # we ARE the right member, block remote auth
            credentials['opencore_auth_match'] = True
            if hasher.validate(hashed, password):
                # AND the password was right
                return True
            else:
                # password was wrong
                return False
        else:
            # we're not even the right member object
            return False

    security.declarePrivate('post_validate')
    def post_validate(self, REQUEST, errors):
        FolderishMember.post_validate(self, REQUEST, errors)
        form = REQUEST.form
        if form.has_key('password'):
            password = form.get('password', None)
            confirm = form.get('confirm_password', None)
            
            if not errors.get('password', None):
                if password and password == 'password':
                    errors['password'] = \
                        self.translate('id_pass_password',
                                       default='"password" is not a valid password.',
                                       domain='remember-plone')


atapi.registerType(OpenMember, package=PROJECTNAME)
