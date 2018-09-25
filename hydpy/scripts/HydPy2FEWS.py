#!python

import logging
import sys

logging.basicConfig(filename='HydPy2FEWS.log', level=logging.INFO)
try:
    from hydpy.auxs.xmltools import execute_workflow
    execute_workflow(argv=sys.argv)
except BaseException as exc:
    logging.critical('Failed')
