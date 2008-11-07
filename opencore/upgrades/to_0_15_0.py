"""
This should be run after upgrading from opencore 0.14.X
to opencore >= 0.15.0.
"""

from opencore.upgrades.utils import logger
from opencore.upgrades.utils import run_import_step

def reapply_type_information(context):
    result = run_import_step(context, 'typeinfo')
    logger.info(result)
