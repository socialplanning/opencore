"""
Convenience script triggering the P2.5 -> P3.0 migrations
"""

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SpecialUsers import system
from Products.CMFCore.utils import getToolByName
import sys
import transaction

newSecurityManager(None, system)

try:
    portal = sys.argv[1]
except IndexError:
    portal = 'openplans'

from Testing.makerequest import makerequest
app=makerequest(app)
portal = app._getOb(portal)

def run_plone_migrations(context):
    """
    Runs the migrations that are registered w/ Plone's
    portal_migrations tool.
    """
    migtool = getToolByName(context, 'portal_migration')
    if not migtool.needUpgrading():
        return
    inst_version = migtool.getInstanceVersion()

    if 'svn' in inst_version:
        # it's an unreleased version, bump down the version number and
        # use forced upgrade
        inst_version = inst_version.split()[0]
        from Products.CMFPlone.MigrationTool import _upgradePaths
        for vfrom, vto in _upgradePaths.items():
            if vto[0] == inst_version:
                inst_version = vfrom
                break
        req = context.REQUEST
        req.environ['REQUEST_METHOD'] = 'POST'
        req.form = {'force_instance_version': inst_version}
        req.force_instance_version = inst_version
        result = migtool.upgrade(REQUEST=req)
    else:
        result = migtool.upgrade()

    if not migtool.needUpgrading():
        transaction.get().note('Plone migrations run')
        transaction.commit()
    else:
        raise RuntimeError, "Plone migrations failed"

def run_opencore_upgrades(context):
    """
    Runs any upgrades that have been registered with the portal_setup
    tool for the opencore default profile.
    """
    profile_id = 'opencore.configuration:default'
    setuptool = getToolByName(context, 'portal_setup')
    steps = setuptool.listUpgrades(profile_id)
    if steps:
        steps = steps[0]
        step_ids = [step['id'] for step in steps]
        req = context.REQUEST
        req.form = {'profile_id': profile_id,
                    'upgrades': step_ids,
                    'show_old': 1}
        setuptool.manage_doUpgrades(req)
        transaction.get().note('OpenCore upgrade run')
        transaction.commit()

run_plone_migrations(portal)
run_opencore_upgrades(portal)
print "OPENCORE MIGRATION SUCCESS"
