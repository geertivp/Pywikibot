#!/usr/bin/python3

# The helptext is displayed with -h
codedoc = """
Validate a Wikidata item by obtaining the list of matching item numbers and attributes.

Parameters:

    P1: target language

    stdin: the list of item labels

Return status:

    The following status is returned to the shell:

	0 Normal termination
	1 Help requested (-h)
	2 Ctrl-c pressed, program interrupted (multiple Ctrl-c are required when in language update mode)
    3 Invalid or missing parameter
    10 Homonym
    13 Maxlag error
    20 General error

Author:

	Geert Van Pamel, 2022-01-05, GNU General Public License v3.0, User:Geertivp

Prequisites:

    Install Pywikibot client software; see https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
    https://stackoverflow.com/questions/36406862/check-whether-an-item-with-a-certain-label-and-description-already-exists-on-wik
    https://www.mediawiki.org/wiki/Wikibase/API
    https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities

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
from pywikibot.data import api

# Global technical parameters
modnm = 'Pywikibot validate_item'     # Module name (using the Pywikibot package)
pgmid = '2022-01-05 (gvp)'	            # Program ID and version

"""
    Static definitions
"""

# Functional configuration flags

# Technical configuration flags
# Defaults: transparent and safe
debug = False		# Can be activated with -d (errors and configuration changes are always shown)
errorstat = True    # Show error statistics (disable with -e)
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
errwaitfactor = 4	# Extra delay after error; best to keep the default value (maximum delay of 4 x 150 = 600 s = 10 min)
maxdelay = 150		# Maximum error delay in seconds (overruling any extreme long processing delays)
minsucrate = 70.0   # Minimum success rate per target language (the script is stopped below this threshold)

# To be set in user-config.py (what parameters is PAWS using?)
"""
    maxthrottle = 60
    put_throttle = 1, for maximum transaction speed (bot account required)
    noisysleep = 60.0, to avoid the majority/all of the confusing sleep messages
    maxlag = 5, to avoid overloading the servers
    max_retries = 4
    retry_wait = 30
    retry_max = 320
"""


def fatal_error(errcode, errtext):
    """
    A fatal error has occurred; we will print the error messaga, and exit with an error code
    """
    global exitstat

    exitstat = max(exitstat, errcode)
    logger.error(errtext)
    if exitfatal:		# unless we ignore fatal errors
        sys.exit(exitstat)
    else:
        logger.error('Proceed after fatal error')


def wd_proc_all_items():
    """
    """

    global exitstat

# Print preferences
    if verbose or debug:
        print('Verbose mode:\t%s' % verbose)
        print('Debug mode:\t%s' % debug)
        print('Exit on fatal error:\t%s' % exitfatal)
        print('Error wait factor:\t%d' % errwaitfactor)

# Loop initialisation
    transcount = 0	    	# Total transaction counter
    statcount = 0           # Statement count
    pictcount = 0	    	# Picture count
    safecount = 0	    	# Safe transaction
    errcount = 0	    	# Error counter
    errsleep = 0	    	# Technical error penalty (sleep delay in seconds)

# Avoid that the user is waiting for a response while the data is being queried
    if verbose:
        print('\nProcessing statements')

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for newitem in itemlist:	# Main loop for all DISTINCT items

      objectname = ' '.join(newitem.split())    # Remove duplicate spaces
      if qsuffre.search(objectname):
        status = 'Skip'
        errcount += 1
        exitstat = max(exitstat, 3)
        logger.error('Bad name: %s' % (objectname))
      elif objectname > '' and status != 'Stop':	# Ctrl-c pressed -> stop in a proper way

        # Check if item already exists
        params = {'action': 'wbsearchentities', 'format': 'json',
                  'language': mainlang, 'type': 'item',
                  'search': objectname, 'limit': 'max'}
        request = api.Request(site=wikidata_site, parameters=params)
        result = request.submit()

        if debug:
            print(result)

# Get item list from label
# All languages are searched (first match?)
        validatelist = []
        if 'search' in result:
            for res in result['search']:
                validatelist.append(res['id'])

        #print(validatelist)
        for qnumber in validatelist:
            transcount += 1	# New transaction
            status = 'OK'
            label = ''
            descr = ''
            alias = []
            commonscat = '' # Commons category
            nationality = ''
            birthday = ''
            deathday = ''

            item = pywikibot.ItemPage(repo, qnumber)
            item.get(get_redirect = True)

            if mainlang in item.labels:
                label = item.labels[mainlang]

            if mainlang in item.descriptions:
                descr = item.descriptions[mainlang]

            if mainlang in item.aliases:
                alias = item.aliases[mainlang]

# Get Commons category/creator
            if 'P373' in item.claims:       # Wikimedia Commons Category
                commonscat = item.claims['P373'][0].getTarget()
            elif 'P1472' in item.claims:    # Wikimedia Commons Creator
                commonscat = item.claims['P1472'][0].getTarget()

            if 'P27' in item.claims:
                for seq in item.claims['P27']:          # Get nationality
                    val = seq.getTarget()
                    try:                    # Catch empty value
                        val.get(get_redirect = True)    # To get the label
                        nationality += val.labels[mainlang] + '/'
                    except:
                        pass

            if 'P569' in item.claims:       # Get birth date (normally only one)
                val = item.claims['P569'][0].getTarget()
                try:
                    birthday = val.year
                except:
                    pass

            if 'P570' in item.claims:       # Get death date (normally only one)
                val = item.claims['P570'][0].getTarget()
                try:
                    deathday = val.year
                except:
                    pass

            try:
                pass

# (14) Error handling
            except KeyboardInterrupt:
                status = 'Stop'	# Ctrl-c trap; process next language, if any
                exitstat = max(exitstat, 2)

            except pywikibot.exceptions.MaxlagTimeoutError as error:  # Attempt error recovery
                logger.error('Error updating %s, %s' % (qnumber, error))
                status = 'Error'	    # Handle any generic error
                errcount += 1
                exitstat = max(exitstat, 20)
                deltasecs = int((datetime.now() - now).total_seconds())	# Calculate technical error penalty
                if deltasecs >= 30: 	# Technical error; for transactional errors there is no wait time increase
                    errsleep += errwaitfactor * min(maxdelay, deltasecs)
                    # Technical errors get additional penalty wait
                    # Consecutive technical errors accumulate the wait time, until the first successful transaction
                    # We limit the delay to a multitude of maxdelay seconds
                if errsleep > 0:    	# Allow the servers to catch up; slowdown the transaction rate
                    logger.error('%d seconds maxlag wait' % (errsleep))
                    time.sleep(errsleep)

            except Exception as error:  # other exception to be used
                logger.error('Error updating %s, %s' % (qnumber, error))
                status = 'Error'	    # Handle any generic error
                errcount += 1
                exitstat = max(exitstat, 20)
                if exitfatal:           # Stop on first error
                    raise

            """
        The transaction was either executed correctly, or an error occurred.
        Possibly already a system error message was issued.
        We will report the results here, as much as we can, one line per item.
            """

    # Get the elapsed time in seconds and the timestamp in string format
            prevnow = now	        	# Transaction status reporting
            now = datetime.now()	    # Refresh the timestamp to time the following transaction

            if verbose or status not in ['OK']:		# Print transaction results
                isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Only needed to format output
                totsecs = (now - prevnow).total_seconds()	# Elapsed time for this transaction
                print('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, qnumber, label, commonscat, alias, nationality, birthday, deathday, descr))


def show_help_text():
# Show program help and exit (only show head text)
    helptxt = helpre.search(codedoc)
    if helptxt:
        print(helptxt.group(0))	# Show helptext
    sys.exit(1)         # Must stop


def show_prog_version():
# Show program version
    print('%s version %s' % (modnm, pgmid))


def get_next_param():
    """
    Get the next command parameter, and handle any qualifiers
    """

    global debug
    global errwaitfactor
    global exitfatal
    global verbose

    cpar = sys.argv.pop(0)	    # Get next command parameter
    if debug:
        print('Parameter %s' % cpar)

    if cpar.startswith('-d'):	# debug mode
        debug = True
        print('Setting debug mode')
    elif cpar.startswith('-e'):	# error stat
        errorstat = False
        print('Disable error statistics')
    elif cpar.startswith('-h'):	# help
        show_help_text()
    elif cpar.startswith('-m'):	# fast mode
        errwaitfactor = 1
        print('Setting fast mode')
    elif cpar.startswith('-p'):	# proceed after fatal error
        exitfatal = False 
        print('Setting proceed after fatal error')
    elif cpar.startswith('-q'):	# quiet mode
        verbose = False 
        print('Setting quiet mode')
    elif cpar.startswith('-v'):	# verbose mode
        verbose = True
        print('Setting verbose mode')
    elif cpar.startswith('-V'):	# Version
        show_prog_version()
    elif cpar.startswith('-'):	# unrecognized qualifier (fatal error)
        fatal_error(4, 'Unrecognized qualifier; use -h for help')
    return cpar		# Return the parameter or the qualifier to the caller


# Main program entry
# First identify the program
logger = logging.getLogger('validate_item')

if verbose:
    show_prog_version()	    	# Print the module name

try:
    pgmnm = sys.argv.pop(0)	    # Get the name of the executable
    if debug:
        print('%s version %s' % (pgmnm, pgmid)) # Physical program
except:
    shell = False
    print('No shell available')	# Most probably running on PAWS Jupyter

"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""

helpre = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+')  # Help text
humsqlre = re.compile(r'\s*#.*\n')          # Human readable query, remove all comments including LF
comsqlre = re.compile(r'\s+')		        # Computer readable query, remove duplicate whitespace
urlbre = re.compile(r'[^\[\]]+')	        # Remove URL square brackets (keep the article page name)
suffre = re.compile(r'\s*[(,]')		        # Remove () and , suffix (keep only the base label)
langre = re.compile(r'^[a-z]{2,3}$')        # Verify for valid ISO 639-1 language codes
propre = re.compile(r'P[0-9]+')             # P-number
qsuffre = re.compile(r'Q[0-9]+')            # Q-number

inlang = '-'
while len(sys.argv) > 0 and inlang.startswith('-'):
    inlang = get_next_param().lower()

# Global parameters
mainlang = os.getenv('LANG', 'nl')[:2]     # Default description language
if langre.search(inlang):
    mainlang = inlang
else:
    inlang = mainlang

if verbose or debug:
    print('Main language:\t%s' % mainlang)
    print('Maximum delay:\t%d s' % maxdelay)
    print('Minimum success rate:\t%f%%' % minsucrate)

# Get list of item numbers
inputfile = sys.stdin.read()
itemlist = sorted(set(inputfile.split('\n')))
if debug:
    print(itemlist)

# Connect to database
transcmt = 'Pwb validate item'	    	    # Wikidata transaction comment
wikidata_site = pywikibot.Site('wikidata', 'wikidata')  # Login to Wikibase instance
repo = wikidata_site.data_repository()

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