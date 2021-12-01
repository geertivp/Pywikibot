#!/usr/bin/python3

# The helptext is displayed with -h
codedoc = """
Get a list of items.

Prequisites:


Parameters:

    stdin:

        Item list

Return status:

    The following status is returned to the shell:

	0 Normal termination
	1 Help requested (-h)
	2 Ctrl-c pressed, program interrupted
	3 Invalid or missing parameter
    20 General error

Author:

	Geert Van Pamel, 2021-11-30, GNU General Public License v3.0, User:Geertivp

Documentation:

"""

# List the required modules
import logging          # Error logging
import os               # Operating system: getenv
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import urllib.parse     # URL encoding/decoding (e.g. Wikidata Query URL)

import pywikibot		# API interface to Wikidata
from datetime import datetime	# now, strftime, delta time, total_seconds

# Global technical parameters
modnm = 'Pywikibot get_item_regex'    # Module name (using the Pywikibot package)
pgmid = '2021-11-30 (gvp)'	         # Program ID and version

# Defaults: transparent and safe
debug = False		# Can be activated with -d (errors and configuration changes are always shown)
exitfatal = True	# Exit on fatal error (can be disabled with -p; please take care)
shell = True		# Shell available (command line parameters are available; automatically overruled by PAWS)
verbose = True		# Can be set with -q or -v (better keep verbose to monitor the bot progress)

# Technical parameters

"""
    Default error penalty wait factor (can be overruled with -f).
    Larger values ensure that maxlag errors are avoided, but temporarily delay processing.
    It is advised not to overrule this value.
"""

exitstat = 0        # (default) Exit status


def wd_proc_all_items():
    """
    """

    global exitstat

# Process all items in the list
    for qnumber in itemlist:	# Main loop for all DISTINCT items
        print(qnumber)


def show_prog_version():
# Show program version
    print('%s version %s' % (modnm, pgmid))


# Main program entry
# First identify the program
logger = logging.getLogger('get_item_regex')

if verbose:
    show_prog_version()	    	# Print the module name

try:
    pgmnm = sys.argv.pop(0)	    # Get the name of the executable
    if debug:
        print('%s version %s' % (pgmnm, pgmid)) # Physical program
except:
    shell = False
    logger.error('No shell available')	# Most probably running on PAWS Jupyter

"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""

qsuffre = re.compile(r'Q[0-9]+')             # Q-number

# Get list of item numbers
inputfile = sys.stdin.read()
itemlist = sorted(set(qsuffre.findall(inputfile)))
if debug:
    print(itemlist)

wd_proc_all_items()	# Execute all items for one language

"""
    Print all sitelinks (base addresses)
    PAWS is using tokens (passwords can't be used because Python scripts are public)
    Shell is using passwords (from user-password.py file)
"""
if debug:
    for site in sorted(pywikibot._sites.values()):
        if site.username():
            print(site, site.username(), site.is_oauth_token_available(), site.logged_in())

sys.exit(exitstat)

# Einde van de miserie
"""

"""
