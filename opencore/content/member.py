from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCorePermissions import *

import Products.Archetypes.public as atapi
from Products.Archetypes.ExtensibleMetadata import ExtensibleMetadata
from Products.Archetypes.ArchetypeTool import base_factory_type_information as bfti

from types import TupleType, ListType, UnicodeType
from Products.Archetypes.Field import STRING_TYPES

from Products.remember.content.member_schema \
     import id_schema, contact_schema, plone_schema, \
     security_schema, login_info_schema
from Products.remember.content.member import FolderishMember

from Products.TeamSpace.security import TeamSecurity

from Products.OpenPlans.config import PROJECTNAME

member_schema = id_schema + contact_schema + plone_schema + \
                security_schema + login_info_schema
content_schema = member_schema.copy() # copy before editing

# specify which fields are searchable in the roster
content_schema['id'].rosterSearch = 1
content_schema['fullname'].rosterSearch = 1
content_schema['location'].rosterSearch = 1

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

class OpenMember(TeamSecurity, FolderishMember):
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

    # team security support
    def _getTeamsForLocalRoles(self):
        """
        return the teams for which the member has an active
        membership
        """
        return self.getActiveTeams()

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

atapi.registerType(OpenMember, package=PROJECTNAME)
