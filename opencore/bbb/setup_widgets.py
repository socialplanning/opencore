from Products.CMFPlone import MigrationTool
from Products.OpenPlans.Extensions.setup import TOPPSetup, NuiSetup

MigrationTool.registerSetupWidget(TOPPSetup)
MigrationTool.registerSetupWidget(NuiSetup)
