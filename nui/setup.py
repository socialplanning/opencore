import os
from pprint import pprint

from topp.utils import config

from Products.CMFCore.utils import getToolByName

from Products.OpenPlans.Extensions.setup import convertFunc, reinstallTypes, \
     reinstallWorkflows
from Products.OpenPlans.Extensions.Install import install_workflow_map, \
     installNewsFolder, securityTweaks
from Products.OpenPlans.Extensions.Install import setupPeopleFolder, \
     setupProjectLayout, setupHomeLayout
from Products.OpenPlans.Extensions.Install import createMemIndexes, \
     installColumns, createValidationMember, \
     install_local_transient_message_utility, install_email_invites_utility
from Products.OpenPlans.Extensions.utils import reinstallSubskins
from Products.OpenPlans import config as op_config
from indexing import createIndexes

HERE = os.path.dirname(__file__)
ALIASES = os.path.join(HERE, 'aliases.cfg')

def save_all_projects(portal, out):
    # separate widget for fixes?
    catalog = getToolByName(portal, 'portal_catalog')
    brains = catalog(portal_type='OpenProject')
    projects = (b.getObject() for b in brains)
    for project in projects:
        title = project.Title()
        values = dict(title=title)
        project.processForm(values=values)
        out.write('processed project: %s\n' % title)
    return out.getvalue()

def reindex_membrane_tool(portal, out):
    # requires the types to be reinstalled first
    reinstallTypes(portal, portal)
    mbtool = getToolByName(portal, 'membrane_tool')
    mbtool.reindexIndex('getLocation', portal.REQUEST)
    print >> out, "getLocation reindexed" 

def move_interface_marking_on_projects_folder(portal, out):
    #XX needed? test?
    from Products.Five.utilities.marker import erase
    from zope.interface import alsoProvides
    from opencore.interfaces import IAddProject
    import sys
    import opencore
    sys.modules['Products.OpenPlans.interfaces.adding'] = opencore.interfaces.adding
    pf = portal.projects
    erase(pf, IAddProject)
    alsoProvides(pf, IAddProject)
    print >> out, "Fixed up interfaces"

def migrate_wiki_attachments(portal, out):
    catalog = getToolByName(portal, 'portal_catalog')
    query = dict(portal_type='FileAttachment')
    brains = catalog(**query)
    objs = (b.getObject() for b in brains)
    out.write('beginning attachment title migration\n')
    for attach in objs:
        if not attach.Title():
            attach_id = attach.getId()
            out.write('Adding title to %s\n' % attach_id)
            attach.setTitle(attach_id)
    out.write('attachment title migration complete\n')
    return out.getvalue()

def set_method_aliases(portal, out):
    pt = getToolByName(portal, 'portal_types')
    amap = config.ConfigMap.load(ALIASES)
    out.write('Setting method aliases::')
    for type_name in amap:
        out.write('<< %s >>\n' %type_name)
        fti = getattr(pt, type_name)
        aliases = fti.getMethodAliases()
        new = amap[type_name]

        # compensate for cfgparser lowercasing
        if new.has_key('(default)'):
            new['(Default)']=new['(default)']
            del new['(default)']
            
        aliases.update(new)
        fti.setMethodAliases(aliases)
        out.write('%s' %pprint(aliases, out))

def migrate_portraits(portal, out):
    for member in portal.portal_memberdata.objectValues():
        if hasattr(member, 'portrait_thumb'):continue
        old_portrait = member.getPortrait()
        if old_portrait:
            member.setPortrait(old_portrait)

nui_functions = dict(createMemIndexes=convertFunc(createMemIndexes),
                     installNewsFolder=convertFunc(installNewsFolder),
                     move_interface_marking_on_projects_folder=convertFunc(move_interface_marking_on_projects_folder),
                     reindex_membrane_tool=convertFunc(reindex_membrane_tool),
                     save_all_projects=convertFunc(save_all_projects),
                     setupHomeLayout=convertFunc(setupHomeLayout),
                     setupPeopleFolder=convertFunc(setupPeopleFolder),
                     setupProjectLayout=convertFunc(setupProjectLayout),
                     securityTweaks=convertFunc(securityTweaks),
                     installMetadataColumns=convertFunc(installColumns),
                     reinstallSubskins=reinstallSubskins,
                     migrate_wiki_attachments=convertFunc(migrate_wiki_attachments),
                     createValidationMember=convertFunc(createValidationMember),
                     reinstallWorkflows=reinstallWorkflows,
                     setup_transient_message_utility=convertFunc(install_local_transient_message_utility),
                     install_email_invites_utility=convertFunc(install_email_invites_utility),
                     createIndexes=convertFunc(createIndexes),
                     )

nui_functions['Update Method Aliases']=convertFunc(set_method_aliases)
nui_functions['Migrate portraits (add new sizes)']=convertFunc(migrate_portraits)

def run_nui_setup(portal):
    pm = portal.portal_migration
    import transaction as txn
    pm.alterItems('TOPP Setup', items=['NUI_setup'])
    txn.commit()
    
